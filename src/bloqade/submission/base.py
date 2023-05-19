from bloqade.submission.ir import QuantumTaskIR
from pydantic import BaseModel
from bloqade.submission.capabilities import get_capabilities
from bloqade.submission.quera_api_client.ir.capabilities import QuEraCapabilities


class SubmissionBackend(BaseModel):
    def get_capabilities(self) -> QuEraCapabilities:
        return get_capabilities()

    def validate_task(self, task_ir: QuantumTaskIR):
        raise NotImplementedError

    def submit_task(self, task_ir: QuantumTaskIR):
        raise NotImplementedError

    def cancel_task(self, task_id: str):
        raise NotImplementedError

    def task_results(self, task_id: str):
        raise NotImplementedError

    def task_status(self, task_id: str):
        raise NotImplementedError
