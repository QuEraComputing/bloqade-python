from bloqade.submission.base import SubmissionBackend, ValidationError
from bloqade.submission.ir.braket import (
    from_braket_task_results,
    from_braket_status_codes,
    to_braket_task,
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
        if task.state() == "COMPLETED":
            return from_braket_task_results(task.result())
        else:
            return QuEraTaskResults(
                task_status=from_braket_status_codes(task.state()), shot_outputs=[]
            )

    @property
    def device(self) -> AwsDevice:
        return AwsDevice(self.device_arn)

    def submit_task(self, task_ir: QuEraTaskSpecification) -> str:
        shots, ahs_program = to_braket_task(task_ir)
        task = self.device.run(ahs_program, shots=shots)
        return task.id

    def task_results(self, task_id: str) -> QuEraTaskResults:
        task = AwsQuantumTask(task_id)
        return self._convert_task_results(task)

    def cancel_task(self, task_id: str) -> None:
        AwsQuantumTask(task_id).cancel()

    def task_status(self, task_id: str) -> QuEraTaskStatusCode:
        task = AwsQuantumTask(task_id)
        return self._convert_status_codes(task.state())

    def validate_task(self, task_ir: QuEraTaskSpecification):
        print("validate task called!")
        try:
            task_id = self.submit_task(task_ir)
        except Exception as e:
            if "ValidationException" in str(e) and "validation error" in str(e):
                raise ValidationError(str(e))
            else:
                raise e

        # don't want the task to actually run
        self.cancel_task(task_id)
