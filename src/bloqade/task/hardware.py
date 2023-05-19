from pydantic import BaseModel
from bloqade.submission.quera_api_client.ir.task_results import (
    QuEraTaskResults,
    QuEraShotStatusCode,
)

from bloqade.submission.mock import DumbMockBackend

from bloqade.submission.quera import QuEraBackend
from bloqade.submission.braket import BraketBackend
from bloqade.submission.ir import BraketTaskSpecification
from bloqade.submission.quera_api_client.ir.task_specification import (
    QuEraTaskSpecification,
)
from bloqade.submission.quera_api_client.ir.task_results import QuEraTaskStatusCode

from .base import Task, TaskFuture, BatchFuture, Batch, Report

from typing import Optional, Union, TextIO, List

import json
import numpy as np
import pandas as pd


class TaskDataModel(BaseModel):
    # note that the separate types here are because pydantic
    # will automatically convert between the types in a Union
    quera_task_ir: Optional[QuEraTaskSpecification] = None
    braket_task_ir: Optional[BraketTaskSpecification] = None
    mock_backend: Optional[DumbMockBackend] = None
    quera_backend: Optional[QuEraBackend] = None
    braket_backend: Optional[BraketBackend] = None

    def json(self, exclude_none=True, by_alias=True, **json_options):
        return super().json(
            exclude_none=exclude_none, by_alias=by_alias, **json_options
        )

    def write_json(
        self, filename_or_io: Union[str, TextIO], mode: str = "w", **json_options
    ):
        match filename_or_io:
            case str(filename):
                with open(filename, mode) as io:
                    io.write(self.json(**json_options))
            case _:
                filename_or_io.write(self.json(**json_options))

    def read_json(self, filename_or_io: Union[str, TextIO]):
        match filename_or_io:
            case str(filename):
                with open(filename, "r") as io:
                    params = json.load(io)
            case _:
                params = json.load(filename_or_io)

        braket_backend = params.get("braket_backend")
        if braket_backend:
            self.braket_backend = BraketBackend(**braket_backend)

        quera_backend = params.get("quera_backend")
        if quera_backend:
            self.quera_backend = QuEraBackend(**quera_backend)

        mock_backend = params.get("mock_backend")
        if mock_backend:
            self.mock_backend = DumbMockBackend(**mock_backend)

        quera_task_ir = params.get("quera_task_ir")
        if quera_task_ir:
            self.quera_task_ir = QuEraTaskSpecification(**quera_task_ir)

        braket_task_ir = params.get("braket_task_ir")
        if braket_task_ir:
            self.braket_task_ir = BraketTaskSpecification(**braket_task_ir)

    def _check_fields(self):
        if self.quera_task_ir is None and self.braket_task_ir is None:
            raise AttributeError("Missing task_ir.")

        if (
            self.braket_backend is None
            and self.mock_backend is None
            and self.quera_backend is None
        ):
            raise AttributeError("No backend found for hardware task.")


class HardwareTask(TaskDataModel, Task):
    def submit(self) -> "HardwareTaskFuture":
        self._check_fields()
        if self.braket_backend:
            task_id = self.braket_backend.submit_task(self.braket_task_ir)
            return HardwareTaskFuture(
                task_id=task_id,
                braket_task_ir=self.braket_task_ir,
                braket_backend=self.braket_backend,
            )
        if self.quera_backend:
            task_id = self.quera_backend.submit_task(self.quera_task_ir)
            return HardwareTaskFuture(
                task_id=task_id,
                quera_task_ir=self.quera_task_ir,
                quera_backend=self.quera_backend,
            )
        if self.mock_backend:
            task_id = self.mock_backend.submit_task(self.quera_task_ir)
            return HardwareTaskFuture(
                task_id=task_id,
                quera_task_ir=self.quera_task_ir,
                mock_backend=self.mock_backend,
            )

    def run_validation(self) -> None:
        self._check_fields()

        if self.braket_backend:
            self.braket_backend.validate_task(self.braket_task_ir)

        if self.quera_backend:
            self.quera_backend.validate_task(self.quera_task_ir)

        if self.mock_backend:
            self.mock_backend.validate_task(self.quera_task_ir)


class TaskFutureDataModel(TaskDataModel):
    task_id: Optional[str] = None
    task_result_ir: Optional[QuEraTaskResults] = None

    def read_json(self, filename_or_io: Union[str, TextIO]):
        super().read_json(filename_or_io)

        match filename_or_io:
            case str(filename):
                with open(filename, "r") as io:
                    params = json.load(io)
            case _:
                params = json.load(filename_or_io)

        self.task_id = params.get("task_id")

        task_result_ir = params.get("task_result_ir")
        if task_result_ir:
            self.task_result_ir = QuEraTaskResults(**task_result_ir)

    def _check_fields(self):
        super()._check_fields()

        if self.task_id is None:
            raise AttributeError("Missing task_id.")


class HardwareTaskFuture(TaskFutureDataModel, TaskFuture):
    @property
    def task_results(self) -> QuEraTaskResults:
        if self.task_result_ir:
            return self.task_result_ir

        self.task_result_ir = self.fetch()
        return self.task_result_ir

    def report(self) -> "HardwareTaskReport":
        return HardwareTaskReport(self)

    def status(self) -> None:
        self._check_fields()

        if self.braket_backend:
            self.braket_backend.task_status(self.task_id)

        if self.quera_backend:
            self.quera_backend.task_status(self.task_id)

        if self.mock_backend:
            self.mock_backend.task_status(self.task_id)

    def cancel(self) -> None:
        self._check_fields()
        if self.status() in [
            QuEraTaskStatusCode.Complete,
            QuEraTaskStatusCode.Running,
            QuEraTaskStatusCode.Accepted,
        ]:
            return

        if self.braket_backend:
            self.braket_backend.cancel_task(self.task_id)

        if self.quera_backend:
            self.quera_backend.cancel_task(self.task_id)

        if self.mock_backend:
            self.mock_backend.cancel_task(self.task_id)

    def fetch(self) -> QuEraTaskResults:
        self._check_fields()
        if self.braket_backend:
            return self.braket_backend.task_results(self.task_id)

        if self.quera_backend:
            return self.quera_backend.task_results(self.task_id)

        if self.mock_backend:
            return self.mock_backend.task_results(self.task_id)


class HardwareBatch(Batch, BaseModel):
    tasks: List[HardwareTask]
    task_submit_order: List[int]

    def __init__(self, tasks: List[HardwareTask], task_submit_order=None):
        if task_submit_order is None:
            task_submit_order = list(np.random.permutation(len(tasks)))

        super().__init__(tasks=tasks, task_submit_order=task_submit_order)

    def submit(self):
        try:
            self.tasks[0].run_validation()
            has_validation = True
        except NotImplementedError:
            has_validation = False

        if has_validation:
            for task in self.tasks[1:]:
                task.run_validation()

        # submit tasks in random order but store them
        # in the original order of tasks.
        futures = [None for task in self.tasks]
        for task_index in self.task_submit_order:
            try:
                futures[task_index] = self.tasks[task_index].submit()
            except BaseException as e:
                for future in futures:
                    if future is not None:
                        future.cancel()
                raise e

        return HardwareBatchFuture(futures=futures)


class HardwareBatchFuture(BatchFuture, BaseModel):
    futures: List[HardwareTaskFuture]

    def report(self) -> "HardwareBatchReport":
        return HardwareBatchReport(self)

    def cancel(self):
        for future in self.futures:
            future.cancel()

    def fetch(self):
        task_result_ir_list = []
        for future in self.futures:
            task_result_ir_list.append(future.fetch())

        return task_result_ir_list

    @property
    def task_results(self):
        return [future.task_results for future in self.futures]


# TODO: Implement Multiplex decoding
class HardwareTaskReport(Report):
    def __init__(self, future: HardwareTaskFuture):
        self._future = future
        super().__init__()

    @property
    def future(self):
        return self._future

    def construct_dataframe(self):
        index = []
        data = []
        for shot in self.task_results.shot_outputs:
            pre_sequence = "".join(map(str, shot.pre_sequence))
            key = (pre_sequence,)
            index.append(key)
            data.append(shot.post_sequence)

        index = pd.MultiIndex.from_tuples(index, names=["status_code", "pre_sequence"])

        df = pd.DataFrame(data, index=index)
        df.sort_index()

        return df

    def get_task_filling(self) -> str:
        if self.future.quera_task_ir:
            filling = self.future.quera_task_ir.lattice.filling

        if self.future.braket_task_ir:
            filling = self.future.braket_task_ir.program.setup.ahs_register.filling

        return "".join(map(str, filling))

    def construct_bitstring(self):
        perfect_filling = self.get_task_filling()
        return self.dataframe.loc[perfect_filling].to_numpy()

    def rydberg_densities(self):
        perfect_filling = "".join(map(str, self.get_task_filling()))
        return self.dataframe.loc[perfect_filling].mean()


class HardwareBatchReport(Report):
    def __init__(self, future: HardwareBatchFuture):
        self._future = future
        super().__init__()

    @property
    def future(self):
        return self._future

    def construct_dataframe(self):
        index = []
        data = []
        for task_number, future in enumerate(self.future.futures):
            for shot in future.task_results.shot_outputs:
                pre_sequence = "".join(map(str, shot.pre_sequence))
                if shot.shot_status != QuEraShotStatusCode.Completed:
                    continue
                key = (pre_sequence, task_number)

                index.append(key)
                data.append(shot.post_sequence)

        index = pd.MultiIndex.from_tuples(index, names=["pre_sequence", "task_number"])

        df = pd.DataFrame(data, index=index)
        df.sort_index(axis="index")

        return df

    def get_task_filling(self) -> str:
        fillings = {}
        for task_number, future in enumerate(self.future.futures):
            if future.quera_task_ir:
                filling = future.quera_task_ir.lattice.filling

            if future.braket_task_ir:
                filling = future.braket_task_ir.program.setup.ahs_register.filling
            filling = "".join(map(str, filling))

            fillings[filling] = fillings.get(filling, []) + [task_number]

        if len(fillings) > 1:
            # TODO: figure out how to allow for more than one mask here
            raise ValueError(
                "multiple fillings found in batch task, cannot post-process batch"
            )

        (filing,) = fillings.keys()

        return filling

    def construct_bitstring(self):
        perfect_filling = self.get_task_filling()
        return self.dataframe.loc[perfect_filling].to_numpy()

    def rydberg_densities(self):
        perfect_filling = "".join(map(str, self.get_task_filling()))
        return self.dataframe.loc[perfect_filling].mean()
