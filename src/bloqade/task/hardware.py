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

from typing import Optional, Union, TextIO
import json


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

    def _validate_fields(self):
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
        self._validate_fields()
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

    def validate(self) -> None:
        self._validate_fields()

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

    def _validate_fields(self):
        super()._validate_fields()

        if self.task_id is None:
            raise AttributeError("Missing task_id.")


class HardwareTaskFuture(TaskFutureDataModel, TaskFuture):
    def status(self) -> None:
        self._validate_fields()

        if self.braket_backend:
            self.braket_backend.task_status(self.task_id)

        if self.quera_backend:
            self.quera_backend.task_status(self.task_id)

        if self.mock_backend:
            self.mock_backend.task_status(self.task_id)

    def cancel(self) -> None:
        self._validate_fields()
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
        self._validate_fields()
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
