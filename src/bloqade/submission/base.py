from bloqade.submission.ir.braket import BraketTaskSpecification
from bloqade.submission.ir.task_specification import QuEraTaskSpecification
from typing import Union
from pydantic import BaseModel


class SubmissionBackend(BaseModel):
    def validate_task(
        self, task_ir: Union[BraketTaskSpecification, QuEraTaskSpecification]
    ):
        raise NotImplementedError

    def submit_task(
        self, task_ir: Union[BraketTaskSpecification, QuEraTaskSpecification]
    ):
        raise NotImplementedError

    def cancel_task(self, task_id: str):
        raise NotImplementedError

    def task_results(self, task_id: str):
        raise NotImplementedError

    def task_status(self, task_id: str):
        raise NotImplementedError
