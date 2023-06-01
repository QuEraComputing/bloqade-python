from bloqade.submission.ir.task_results import (
    QuEraTaskResults,
    QuEraTaskStatusCode,
    QuEraShotStatusCode,
)
from bloqade.submission.ir.parallel import ParallelDecoder
from typing import List, Union, TextIO, Tuple, Optional
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
        return self.fetch(cache=True)

    def fetch(self, cache=False) -> QuEraTaskResults:
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
    def _task_list(self) -> List[Task]:
        raise NotImplementedError

    def _emit_future(self, futures: List[TaskFuture]) -> "Future":
        raise NotImplementedError

    def submit(self, submission_order: Optional[List[int]] = None) -> "Future":
        task_list = self._task_list()

        if submission_order is None:
            submission_order = np.random.permutation(len(task_list))

        if sorted(submission_order) != list(range(len(task_list))):
            raise ValueError("Submission order must be a permutation of the tasks.")

        try:
            task_list[0].run_validation()
            has_validation = True
        except NotImplementedError:
            has_validation = False

        if has_validation:
            for task in task_list[1:]:
                task.run_validation()

        # submit tasks in random order but store them
        # in the original order of tasks.
        futures = [None for _ in task_list]
        for task_index in submission_order:
            try:
                futures[task_index] = task_list[task_index].submit()
            except BaseException as e:
                for future in futures:
                    if future is not None:
                        future.cancel()
                raise e

        return self._emit_future(futures)


class Future:
    @property
    def task_results(self) -> List[QuEraTaskResults]:
        return [future.task_result for future in self.futures_list()]

    def report(self) -> "Report":
        return Report(self)

    def cancel(self) -> None:
        for future in self.futures_list():
            future.cancel()

    def futures_list(self) -> List[TaskFuture]:
        raise NotImplementedError


# NOTE: this is only the basic report, we should provide
#      a way to customize the report class,
#      e.g result.plot() returns a `TaskPlotReport` class instead
class Report:
    def __init__(self, future: Future) -> None:
        self._future = future
        self._dataframe = None  # df cache
        self._bitstrings = None  # bitstring cache

    @property
    def future(self) -> Future:
        return self._future

    @property
    def task_results(self) -> List[QuEraTaskResults]:
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

        for task_number, task_future in enumerate(self.future.futures_list()):
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
        bitstrings = []
        task_numbers = filtered_df.index.get_level_values("task_number")
        for task_number in task_numbers.unique():
            bitstrings.append(filtered_df.loc[task_number, ...].to_numpy())

        return bitstrings

    def rydberg_densities(self) -> pd.Series:
        perfect_sorting = self.dataframe.index.get_level_values("perfect_sorting")
        pre_sequence = self.dataframe.index.get_level_values("pre_sequence")

        return (
            self.dataframe.loc[perfect_sorting == pre_sequence]
            .groupby("task_number")
            .mean()
        )
