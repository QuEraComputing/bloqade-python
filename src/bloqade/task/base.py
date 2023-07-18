import datetime
from numbers import Number
from bloqade.submission.base import ValidationError
from bloqade.submission.ir.task_results import (
    QuEraTaskResults,
    QuEraTaskStatusCode,
    QuEraShotStatusCode,
)
from bloqade.submission.ir.parallel import ParallelDecoder
from bloqade.submission.base import SubmissionBackend
from typing import Dict, List, Union, TextIO, Tuple, Optional, Type
from collections import OrderedDict
from numpy.typing import NDArray
from pydantic.dataclasses import dataclass
from pydantic import BaseModel
from itertools import product
import pandas as pd
import numpy as np
import json


@dataclass(frozen=True)
class Geometry:
    sites: List[Tuple[float, float]]
    filling: List[int]
    parallel_decoder: Optional[ParallelDecoder]


class JSONInterface(BaseModel):
    def _init_from_dict(self, **params) -> None:
        raise NotImplementedError

    def json(self, exclude_none=True, by_alias=True, **json_options) -> str:
        return super().json(
            exclude_none=exclude_none, by_alias=by_alias, **json_options
        )

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

        self._init_from_dict(**params)


class Task:
    @property
    def metadata(self) -> Dict[str, Number]:
        return self._metadata()

    @property
    def geometry(self) -> Geometry:
        return self._geometry()

    def _geometry(self) -> Geometry:
        raise NotImplementedError

    def _metadata(self) -> Dict[str, Number]:
        return {}

    def submit(self) -> "TaskFuture":
        raise NotImplementedError

    def run_validation(self) -> None:
        raise NotImplementedError


class SerializableTask(JSONInterface, Task):
    def _backend(self) -> SubmissionBackend:
        raise NotImplementedError

    @property
    def backend(self):
        return self._backend()


class TaskFuture:
    def _task(self) -> Task:
        raise NotImplementedError

    @property
    def task(self) -> Task:
        return self._task()

    @property
    def task_result(self) -> QuEraTaskResults:
        return self.fetch(cache_result=True)

    def fetch(self, cache_result=False) -> QuEraTaskResults:
        raise NotImplementedError

    def status(self) -> QuEraTaskStatusCode:
        raise NotImplementedError

    def cancel(self) -> None:
        raise NotImplementedError


class SerializableTaskFuture(JSONInterface, TaskFuture):
    def _resubmit_if_not_submitted(self) -> "SerializableTaskFuture":
        raise NotImplementedError


class BatchTask:
    def _tasks(self) -> OrderedDict[int, Task]:
        raise NotImplementedError

    def _emit_batch_future(
        self, futures: OrderedDict[int, TaskFuture]
    ) -> "BatchFuture":
        raise NotImplementedError

    @property
    def tasks(self) -> OrderedDict[int, Task]:
        return self._tasks()

    def submit(self) -> "BatchFuture":
        task_dict = self._tasks()

        futures = OrderedDict()
        for task_index, task in task_dict.items():
            futures[task_index] = task.submit()

        return self._emit_batch_future(futures)


class SerializableBatchTask(JSONInterface, BatchTask):
    name: Optional[str] = None

    class SubmissionException(Exception):
        pass

    def _task_future_class(self) -> "Type[TaskFuture]":
        raise NotImplementedError

    def remove_invalid_tasks(self) -> "BatchTask":
        valid_tasks = OrderedDict()

        for task_number, task in self._tasks().items():
            try:
                task.run_validation()
                valid_tasks[task_number] = task
            except ValidationError:
                continue

        return self.__class__(tasks=valid_tasks)

    def submit(self, shuffle_submit_order: bool = True) -> "SerializableBatchFuture":
        task_dict = self._tasks()

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
        futures = OrderedDict()
        errors = OrderedDict()
        for task_index in submission_order:
            task = task_dict[task_index]
            try:
                futures[task_index] = task.submit()
            except BaseException as error:
                TaskFutureType = self._task_future_class()
                futures[task_index] = TaskFutureType(task=task, task_id=None)
                errors[task_index] = {
                    "exception_type": error.__name__,
                    "message": str(error),
                }

        batch_future = self._emit_batch_future(futures)
        if errors:
            time_stamp = datetime.datetime.now()
            if self.name:
                future_file = f"{self.name}-partial-batch-future-{time_stamp}.json"
                error_file = f"{self.name}-partial-batch-errors-{time_stamp}.json"
            else:
                future_file = f"partial-batch-future-{time_stamp}.json"
                error_file = f"partial-batch-errors-{time_stamp}.json"

            with open(future_file, "w") as f:
                f.write(batch_future.json(indent=2))

            with open(error_file, "w") as f:
                json.dump(errors, f, indent=2)

            raise SerializableBatchTask.SubmissionException(
                "One or more error(s) occured during submission, please see "
                "the following files for more information:\n"
                f"  - {future_file}\n  - {error_file}\n"
            )

        return batch_future


class BatchFuture:
    def _task_futures(self) -> OrderedDict[int, TaskFuture]:
        raise NotImplementedError

    @property
    def task_futures(self) -> OrderedDict[int, TaskFuture]:
        return self._task_futures()

    @property
    def task_results(self) -> OrderedDict[int, QuEraTaskResults]:
        return OrderedDict(
            [
                (task_number, future.task_result)
                for task_number, future in self.task_futures.items()
            ]
        )

    def report(self) -> "Report":
        return Report(self)

    def cancel(self) -> None:
        for future in self.task_futures.values():
            future.cancel()


class SerializableBatchFuture(JSONInterface, BatchFuture):
    def resubmit_missing_tasks(self) -> "SerializableBatchFuture":
        new_futures = OrderedDict()
        for task_number, future in self.task_futures.items():
            new_futures[task_number] = future._resubmit_if_not_submitted()

        return self.__class__(futures=new_futures)

    def removing_futures_with_task_id(self) -> "SerializableBatchFuture":
        new_futures = OrderedDict()
        for task_number, future in self.task_futures.items():
            if future.task_id is not None:
                new_futures[task_number] = future

        return self.__class__(futures=new_futures)


# NOTE: this is only the basic report, we should provide
#      a way to customize the report class,
#      e.g result.plot() returns a `TaskPlotReport` class instead
class Report:
    def __init__(self, future: BatchFuture) -> None:
        self._future = future
        self._dataframe = None  # df cache
        self._bitstrings = None  # bitstring cache
        self._counts = None  # counts cache

    @property
    def future(self) -> BatchFuture:
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

        for task_number, task_future in self.future.task_futures.items():
            perfect_sorting = "".join(map(str, task_future.task.geometry.filling))
            parallel_decoder = task_future.task.geometry.parallel_decoder

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
