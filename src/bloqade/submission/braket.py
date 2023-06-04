from bloqade.submission.base import SubmissionBackend
from bloqade.submission.ir.braket import (
    from_braket_task_results,
    from_braket_status_codes,
    to_braket_task_ir,
)
from bloqade.submission.ir.task_results import (
    QuEraTaskStatusCode,
    QuEraTaskResults,
)
from bloqade.submission.ir.task_specification import QuEraTaskSpecification
from braket.aws import AwsDevice, AwsQuantumTask


class BraketBackend(SubmissionBackend):
    device_arn: str = "arn:aws:braket:us-east-1::device/qpu/quera/Aquila"

    def _convert_task_results(self, task: AwsQuantumTask) -> QuEraTaskResults:
        if task.status() == "COMPLETED":
            return from_braket_task_results(task.result())
        else:
            return QuEraTaskResults(
                task_status=from_braket_status_codes(task.status()), shot_outputs=[]
            )

    @property
    def device(self) -> AwsDevice:
        return AwsDevice(self.device_arn)

    def submit_task(self, task_ir: QuEraTaskSpecification) -> str:
        braket_task_ir = to_braket_task_ir(task_ir)
        task = self.device.run(braket_task_ir.program, shots=braket_task_ir.nshots)
        return task.id

    def task_results(self, task_id: str) -> QuEraTaskResults:
        task = AwsQuantumTask(task_id)
        return self._convert_task_results(task)

    def cancel_task(self, task_id: str) -> None:
        AwsQuantumTask(task_id).cancel()

    def task_status(self, task_id: str) -> QuEraTaskStatusCode:
        task = AwsQuantumTask(task_id)
        return self._convert_status_codes(task.state)
