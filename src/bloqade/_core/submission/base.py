from bloqade._core.submission.ir.braket import BraketTaskSpecification
from bloqade._core.submission.ir.task_specification import QuEraTaskSpecification
from bloqade._core.submission.ir.task_results import (
    QuEraTaskResults,
    QuEraTaskStatusCode,
)
from typing import Union
from pydantic import BaseModel, Extra
from bloqade._core.submission.capabilities import get_capabilities
from bloqade._core.submission.ir.capabilities import QuEraCapabilities


class ValidationError(Exception):
    pass


class SubmissionBackend(BaseModel):
    class Config:
        extra = Extra.forbid

    def get_capabilities(self) -> QuEraCapabilities:
        return get_capabilities()

    def validate_task(
        self, task_ir: Union[BraketTaskSpecification, QuEraTaskSpecification]
    ) -> None:
        raise NotImplementedError

    def submit_task(
        self, task_ir: Union[BraketTaskSpecification, QuEraTaskSpecification]
    ) -> str:
        raise NotImplementedError

    def cancel_task(self, task_id: str) -> None:
        raise NotImplementedError

    def task_results(self, task_id: str) -> QuEraTaskResults:
        raise NotImplementedError

    def task_status(self, task_id: str) -> QuEraTaskStatusCode:
        raise NotImplementedError
