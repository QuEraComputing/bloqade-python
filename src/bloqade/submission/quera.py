from bloqade.submission.base import SubmissionBackend, ValidationError
from bloqade.submission.ir.braket import BraketTaskSpecification
from bloqade.submission.quera_api_client.api import QueueApi
from bloqade.submission.ir.task_specification import (
    QuEraTaskSpecification,
)
from bloqade.submission.ir.capabilities import QuEraCapabilities
from bloqade.submission.ir.task_results import (
    QuEraTaskResults,
    QuEraTaskStatusCode,
)
from typing import Optional


class QuEraBackend(SubmissionBackend):
    api_hostname: str
    qpu_id: str
    api_stage: str = "v0"
    proxy: Optional[str] = None
    # Sigv4Request arguments
    region: Optional[str] = None
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    session_token: Optional[str] = None
    session_expires: Optional[int] = None
    role_arn: Optional[str] = None
    role_session_name: Optional[str] = None
    profile: Optional[str] = None

    @property
    def queue_api(self):
        kwargs = {k: v for k, v in self.__dict__.items() if v is not None}
        return QueueApi(**kwargs)

    def get_capabilities(self) -> QuEraCapabilities:
        try:
            return QuEraCapabilities(**self.queue_api.get_capabilities())
        except BaseException:
            return super().get_capabilities()

    def submit_task(self, task_ir: QuEraTaskSpecification) -> str:
        return self.queue_api.post_task(
            task_ir.json(by_alias=True, exclude_none=True, exclude_unset=True)
        )

    def task_results(self, task_id: str) -> QuEraTaskResults:
        return QuEraTaskResults(**self.queue_api.poll_task_results(task_id))

    def cancel_task(self, task_id: str):
        self.queue_api.cancel_task_in_queue(task_id)

    def task_status(self, task_id: str) -> QuEraTaskStatusCode:
        return_body = self.queue_api.get_task_status_in_queue(task_id)
        return QuEraTaskStatusCode(return_body)

    def validate_task(self, task_ir: BraketTaskSpecification | QuEraTaskSpecification):
        try:
            self.queue_api.validate_task(
                task_ir.json(by_alias=True, exclude_none=True, exclude_unset=True)
            )
        except QueueApi.ValidationError as e:
            raise ValidationError(e.body)
