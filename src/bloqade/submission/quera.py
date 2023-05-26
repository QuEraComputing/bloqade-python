from bloqade.submission.base import SubmissionBackend
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
    api_uri: str
    proxy: Optional[str]
    api_version: str
    qpu_id: str

    @property
    def queue_api(self):
        return QueueApi(
            self.api_uri, self.qpu_id, api_version=self.api_version, proxy=self.proxy
        )

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
        return QuEraTaskResults(**self.queue_api.get_task_results(task_id))

    def cancel_task(self, task_id: str):
        self.queue_api.cancel_task_in_queue(task_id)

    def task_status(self, task_id: str) -> QuEraTaskStatusCode:
        return_body = self.queue_api.get_task_summary(task_id)
        return QuEraTaskStatusCode(return_body["status"])
