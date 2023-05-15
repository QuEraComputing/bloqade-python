from bloqade.submission.base import SubmissionBackend
from bloqade.submission.quera_api_client.api import QueueApi
from quera_ahs_utils.quera_ir.task_specification import QuEraTaskSpecification
from quera_ahs_utils.quera_ir.task_results import QuEraTaskResults


class QuEraBackend(SubmissionBackend):
    uri: str
    api_version: str
    qpu_id: str

    @property
    def queue_api(self):
        return QueueApi(self.uri, self.qpu_id, api_version=self.api_version)

    def submit_task(self, task_ir: QuEraTaskSpecification):
        return self.queue_api.post_task(
            task_ir.json(by_alias=True, exclude_none=True, exclude_unset=True)
        )

    def task_results(self, task_id: str) -> QuEraTaskResults:
        return QuEraTaskResults(**self.queue_api.get_task_results(task_id))

    def cancel_task(self, task_id: str):
        return self.queue_api.cancel_task_in_queue(task_id)
