from collections import OrderedDict
from itertools import product
import json
from typing import List, TextIO, Type, TypeVar, Union, Dict, Optional, Tuple
from numbers import Number

import traceback
import datetime
import sys
import os
from pydantic import BaseModel
from bloqade.submission.ir.task_results import (
    QuEraShotStatusCode,
    QuEraTaskResults,
    QuEraTaskStatusCode,
)
from numpy.typing import NDArray
import pandas as pd
import numpy as np
from dataclasses import dataclass
from bloqade.submission.base import ValidationError
from bloqade.submission.ir.parallel import ParallelDecoder


JSONSubType = TypeVar("JSONSubType", bound="JSONInterface")


@dataclass(frozen=True)
class Geometry:
    sites: List[Tuple[float, float]]
    filling: List[int]
    parallel_decoder: Optional[ParallelDecoder] = None


class JSONInterface(BaseModel):
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

    @classmethod
    def load_json(
        cls: Type[JSONSubType], filename_or_io: Union[str, TextIO]
    ) -> JSONSubType:
        if isinstance(filename_or_io, str):
            with open(filename_or_io, "r") as f:
                params = json.load(f)
        else:
            params = json.load(filename_or_io)

        return cls(**params)


@dataclass
class Task:
    task_id: str

    def _geometry(self) -> Geometry:
        raise NotImplementedError(
            f"{self.__class__.__name__}._geometry() not implemented"
        )

    # do we need>?
    def _metadata(self) -> Dict[str, Number]:
        return {}

    # do we need>?
    @property
    def metadata(self) -> Dict[str, Number]:
        return self._metadata()

    @property
    def geometry(self) -> Geometry:
        return self._geometry()

    def validate(self) -> None:
        raise NotImplementedError

    def result(self) -> QuEraTaskResults:
        # this methods hangs until the task is completed
        raise NotImplementedError

    def fetch(self) -> None:
        raise NotImplementedError

    def status(self) -> QuEraTaskStatusCode:
        raise NotImplementedError

    def cancel(self) -> None:
        # this method cancels the task
        raise NotImplementedError


# this class get collection of tasks
# basically behaves as a psudo queuing system
# the user only need to store this objecet
class Batch:
    tasks: OrderedDict[int, Task]
    name: Optional[str] = None

    class SubmissionException(Exception):
        pass

    def cancel(self) -> None:
        for task in self.tasks.values():
            task.cancel()

    def fetch(self) -> None:
        # [TODO]
        for task in self.tasks.values():
            task.fetch()

    def tasks_metric(self):
        # [TODO] print more info on current status
        pass

    def remove_invalid_tasks(self):
        new_tasks = OrderedDict()
        for task_number, task in self.tasks.items():
            try:
                task.run_validation()
                new_tasks[task_number] = task
            except ValidationError:
                continue

        return Batch(new_tasks, name=self.name)

    def submit(self, shuffle_submit_order: bool = True):
        if shuffle_submit_order:
            submission_order = np.random.permutation(list(self.tasks.keys()))
        else:
            submission_order = list(self.tasks.keys())

        for task in self.tasks.values():
            try:
                task.run_validation()
            except NotImplementedError:
                break

        # submit tasks in random order but store them
        # in the original order of tasks.
        # futures = OrderedDict()
        errors = OrderedDict()
        for task_index in submission_order:
            task = self.tasks[task_index]
            try:
                task.submit()
            except BaseException as error:
                # record the error in the error dict
                errors[int(task_index)] = {
                    "exception_type": error.__class__.__name__,
                    "stack trace": traceback.format_exc(),
                }

        if errors:
            time_stamp = datetime.datetime.now()

            if "win" in sys.platform:
                time_stamp = str(time_stamp).replace(":", "~")

            if self.name:
                future_file = f"{self.name}-partial-batch-future-{time_stamp}.json"
                error_file = f"{self.name}-partial-batch-errors-{time_stamp}.json"
            else:
                future_file = f"partial-batch-future-{time_stamp}.json"
                error_file = f"partial-batch-errors-{time_stamp}.json"

            cwd = os.get_cwd()
            # cloud_batch_result.save_json(future_file, indent=2)
            # saving ?

            with open(error_file, "w") as f:
                json.dump(errors, f, indent=2)

            raise Batch.SubmissionException(
                "One or more error(s) occured during submission, please see "
                "the following files for more information:\n"
                f"  - {os.path.join(cwd, future_file)}\n"
                f"  - {os.path.join(cwd, error_file)}\n"
            )

        else:
            # TODO: think about if we should automatically save successful submissions
            #       as well.
            pass

    def get_failed_tasks(self) -> "Batch":
        new_task_results = OrderedDict()
        for task_number, task in self.tasks.items():
            if task.task_id and task.status() in [
                QuEraTaskStatusCode.Failed,
                QuEraTaskStatusCode.Unaccepted,
            ]:
                new_task_results[task_number] = task

        return Batch(new_task_results, name=self.name)

    def remove_failed_tasks(self) -> "Batch":
        new_results = OrderedDict()
        for task_number, cloud_task_result in self.task_results.items():
            if cloud_task_result.status() in [
                QuEraTaskStatusCode.Failed,
                QuEraTaskStatusCode.Unaccepted,
            ]:
                continue
            new_results[task_number] = cloud_task_result

        return Batch(new_results, self.name)

    def report(self) -> "Report":
        ## this potentially can be specialize/disatch
        index = []
        data = []

        for task_number, task in self.tasks.items():
            # this check on result to make sure we don't send request
            if not task.status() == QuEraTaskStatusCode.Completed:
                continue

            geometry = task.geometry
            perfect_sorting = "".join(map(str, geometry.filling))
            parallel_decoder = geometry.parallel_decoder

            if parallel_decoder:
                cluster_indices = parallel_decoder.get_cluster_indices()
            else:
                cluster_indices = {(0, 0): list(range(len(perfect_sorting)))}

            shot_iter = filter(
                lambda shot: shot.shot_status == QuEraShotStatusCode.Completed,
                task.result().shot_outputs,
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

                pfc_sorting = "".join(
                    [perfect_sorting[index] for index in cluster_index]
                )

                key = (
                    task_number,
                    cluster_coordinate,
                    pfc_sorting,
                    pre_sequence,
                )

                index.append(key)
                data.append(post_sequence)

        index = pd.MultiIndex.from_tuples(
            index, names=["task_number", "cluster", "perfect_sorting", "pre_sequence"]
        )

        df = pd.DataFrame(data, index=index)
        df.sort_index(axis="index")

        return Report(df)


# Report is now just a helper class for
# organize and analysis data:
@dataclass
class Report:
    dataframe: pd.DataFrame

    def __init__(self, data) -> None:
        self.dataframe = data  # df
        self._bitstrings = None  # bitstring cache
        self._counts = None  # counts cache

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
