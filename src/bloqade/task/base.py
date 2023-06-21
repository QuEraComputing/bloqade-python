from bloqade.submission.base import ValidationError
from bloqade.submission.ir.task_results import (
    QuEraTaskResults,
    QuEraTaskStatusCode,
    QuEraShotStatusCode,
)
from bloqade.submission.ir.parallel import ParallelDecoder
from typing import List, Union, TextIO, Tuple, Optional
from collections import OrderedDict
from numpy.typing import NDArray
from pydantic.dataclasses import dataclass
from pydantic import BaseModel
from itertools import product
import pandas as pd
import numpy as np
import json


class Task:
    def submit(self) -> "TaskFuture":
        raise NotImplementedError

    def run_validation(self) -> None:
        raise NotImplementedError


@dataclass(frozen=True)
class Geometry:
    sites: List[Tuple[float, float]]
    filling: List[int]
    parallel_decoder: Optional[ParallelDecoder]


class TaskFuture:
    @property
    def geometry(self) -> Geometry:
        return self._task_geometry()

    def _task_geometry(self) -> Geometry:
        raise NotImplementedError

    @property
    def task_result(self) -> QuEraTaskResults:
        return self.fetch(cache_result=True)

    def fetch(self, cache_result=False) -> QuEraTaskResults:
        raise NotImplementedError

    def status(self) -> QuEraTaskStatusCode:
        raise NotImplementedError

    def cancel(self) -> None:
        raise NotImplementedError


class JSONInterface(BaseModel):
    def json(self, exclude_none=True, by_alias=True, **json_options) -> str:
        return super().json(
            exclude_none=exclude_none, by_alias=by_alias, **json_options
        )

    def init_from_dict(self, **params) -> None:
        raise NotImplementedError

    def save_json(
        self, filename_or_io: Union[str, TextIO], mode="w", **json_options
    ) -> None:
        if isinstance(filename_or_io, str):
            with open(filename_or_io, mode) as f:
                f.write(self.json(**json_options))
        else:
            filename_or_io.write(self.json(**json_options))

    def load_json(self, filename_or_io: Union[str, TextIO]) -> None:
        if isinstance(filename_or_io, str):
            with open(filename_or_io, "r") as f:
                params = json.load(f)
        else:
            params = json.load(filename_or_io)

        self.init_from_dict(**params)


class Job:
    def _task_dict(self) -> OrderedDict[int, Task]:
        raise NotImplementedError

    def _emit_future(self, futures: OrderedDict[int, TaskFuture]) -> "Future":
        raise NotImplementedError

    def remove_invalid_tasks(self) -> "Job":
        valid_tasks = OrderedDict()

        for task_number, task in self._task_dict().items():
            try:
                task.run_validation()
                valid_tasks[task_number] = task
            except ValidationError:
                continue

        return self.__class__(tasks=valid_tasks)

    def submit(self, shuffle_submit_order: bool = True) -> "Future":
        task_dict = self._task_dict()

        if shuffle_submit_order:
            submission_order = np.random.permutation(list(task_dict.keys()))
        else:
            submission_order = list(task_dict.keys())

        for task in task_dict.values():
            try:
                task.run_validation()
            except NotImplementedError:
                break

        # submit tasks in random order but store them
        # in the original order of tasks.
        futures = {}
        for task_index in submission_order:
            try:
                futures[task_index] = task_dict[task_index].submit()
            except BaseException as e:
                for future in futures:
                    if future is not None:
                        future.cancel()
                raise e

        return self._emit_future(futures)


class Future:
    @property
    def task_results(self) -> OrderedDict[int, QuEraTaskResults]:
        return OrderedDict(
            [
                (task_number, future.task_result)
                for task_number, future in self.futures_dict().items()
            ]
        )

    def report(self) -> "Report":
        return Report(self)

    def cancel(self) -> None:
        for future in self.futures_dict().values():
            future.cancel()

    def futures_dict(self) -> OrderedDict[int, TaskFuture]:
        raise NotImplementedError


# NOTE: this is only the basic report, we should provide
#      a way to customize the report class,
#      e.g result.plot() returns a `TaskPlotReport` class instead
class Report:
    def __init__(self, future: Future) -> None:
        self._future = future
        self._dataframe = None  # df cache
        self._bitstrings = None  # bitstring cache
        self._counts = None  # counts cache

    @property
    def future(self) -> Future:
        return self._future

    @property
    def task_results(self) -> OrderedDict[int, QuEraTaskResults]:
        return self.future.task_results

    @property
    def dataframe(self) -> pd.DataFrame:
        if self._dataframe is not None:
            return self._dataframe

        self._dataframe = self._construct_dataframe()
        return self._dataframe

    def _construct_dataframe(self) -> pd.DataFrame:
        index = []
        data = []

        for task_number, task_future in self.future.futures_dict().items():
            perfect_sorting = "".join(map(str, task_future.geometry.filling))
            parallel_decoder = task_future.geometry.parallel_decoder

            if parallel_decoder:
                cluster_indices = parallel_decoder.get_cluster_indices()
            else:
                cluster_indices = {(0, 0): list(range(len(perfect_sorting)))}

            shot_iter = filter(
                lambda shot: shot.shot_status == QuEraShotStatusCode.Completed,
                task_future.task_result.shot_outputs,
            )

            for shot, (cluster_coordinate, cluster_index) in product(
                shot_iter, cluster_indices.items()
            ):
                pre_sequence = "".join(
                    map(
                        str,
                        (shot.pre_sequence[index] for index in cluster_index),
                    )
                )

                post_sequence = np.asarray(
                    [shot.post_sequence[index] for index in cluster_index],
                    dtype=np.int8,
                )

                key = (
                    task_number,
                    cluster_coordinate,
                    perfect_sorting,
                    pre_sequence,
                )

                index.append(key)
                data.append(post_sequence)

        index = pd.MultiIndex.from_tuples(
            index, names=["task_number", "cluster", "perfect_sorting", "pre_sequence"]
        )

        df = pd.DataFrame(data, index=index)
        df.sort_index(axis="index")

        return df

    @property
    def markdown(self) -> str:
        return self.dataframe.to_markdown()

    @property
    def bitstrings(self) -> List[NDArray]:
        if self._bitstrings is not None:
            return self._bitstrings
        self._bitstrings = self._construct_bitstrings()
        return self._bitstrings

    def _construct_bitstrings(self) -> List[NDArray]:
        perfect_sorting = self.dataframe.index.get_level_values("perfect_sorting")
        pre_sequence = self.dataframe.index.get_level_values("pre_sequence")
        filtered_df = self.dataframe[perfect_sorting == pre_sequence]
        task_numbers = filtered_df.index.get_level_values("task_number")

        n_atoms = len(perfect_sorting[0])
        bitstrings = [np.zeros((0, n_atoms)) for _ in range(task_numbers.max() + 1)]

        for task_number in task_numbers.unique():
            bitstrings[task_number] = filtered_df.loc[task_number, ...].to_numpy()

        return bitstrings

    @property
    def counts(self) -> List[OrderedDict[str, int]]:
        if self._counts is not None:
            return self._counts
        self._counts = self._construct_counts()
        return self._counts

    def _construct_counts(self) -> List[OrderedDict[str, int]]:
        counts = []
        for bitstring in self.bitstrings:
            output = np.unique(bitstring, axis=0, return_counts=True)
            counts.append(
                {
                    "".join(map(str, unique_bitstring)): bitstring_count
                    for unique_bitstring, bitstring_count in zip(*output)
                }
            )

        return counts

    def rydberg_densities(self) -> pd.Series:
        # TODO: implement nan for missing task numbers
        perfect_sorting = self.dataframe.index.get_level_values("perfect_sorting")
        pre_sequence = self.dataframe.index.get_level_values("pre_sequence")

        return 1 - (
            self.dataframe.loc[perfect_sorting == pre_sequence]
            .groupby("task_number")
            .mean()
        )
