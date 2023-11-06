from pydantic import PrivateAttr
from bloqade.submission.base import SubmissionBackend, ValidationError
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
    virtual_queue: Optional[str] = None
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
    _queue_api: Optional[object] = PrivateAttr(None)

    @property
    def queue_api(self):
        if self._queue_api is None:
            try:
                from qcs.api_client.api import QueueApi
            except ImportError:
                raise RuntimeError("Must install QuEra-QCS-client to use QuEraBackend")

            kwargs = {k: v for k, v in self.__dict__.items() if v is not None}
            self._queue_api = QueueApi(**kwargs)

        return self._queue_api

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

    def validate_task(self, task_ir: QuEraTaskSpecification):
        try:
            self.queue_api.validate_task(
                task_ir.json(by_alias=True, exclude_none=True, exclude_unset=True)
            )
        except self.queue_api.ValidationError as e:
            raise ValidationError(str(e))

    def update_credential(
        self, access_key: str = None, secret_key: str = None, session_token: str = None
    ):
        if secret_key is not None:
            self.secret_key = secret_key
        if access_key is not None:
            self.access_key = access_key
        if session_token is not None:
            self.session_token = session_token
