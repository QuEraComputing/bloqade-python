from pydantic import BaseModel
from bloqade.submission.quera_api_client.ir.task_results import QuEraTaskResults

from bloqade.submission.mock import DumbMockBackend

from bloqade.submission.quera import QuEraBackend
from bloqade.submission.braket import BraketBackend
from bloqade.submission.ir import BraketTaskSpecification
from bloqade.submission.quera_api_client.ir.task_specification import (
    QuEraTaskSpecification,
)
from bloqade.submission.quera_api_client.ir.task_results import QuEraTaskStatusCode

from .base import Task, TaskFuture

from typing import Optional, Union, TextIO, List
import json
import numpy as np


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

    @property
    def task_results(self) -> QuEraTaskResults:
        if self.task_result_ir is None:
            self.task_result_ir = self.fetch()

        return self.task_result_ir


class HardwareBatch(BaseModel):
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


class HardwareBatchFuture(BaseModel):
    futures: List[HardwareTaskFuture]
    task_result_ir_list: List[QuEraTaskResults] = []

    def cancel(self):
        for future in self.futures:
            future.cancel()

    def fetch(self):
        task_result_ir_list = []
        for future in self.futures:
            task_result_ir_list.append(future.fetch())

        return task_result_ir_list

    @property
    def task_result_ir_list(self):
        if self.task_result_ir_list:
            return self.task_result_ir_list

        self.task_result_ir_list = self.fetch()

        return self.task_result_ir_list
