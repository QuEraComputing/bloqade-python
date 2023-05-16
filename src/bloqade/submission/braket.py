from bloqade.submission.base import SubmissionBackend
from bloqade.submission.ir import BraketTaskSpecification
from bloqade.submission.quera_api_client.ir.task_results import (
    QuEraTaskStatusCode,
    QuEraTaskResults,
    QuEraShotResult,
    QuEraShotStatusCode,
)
from braket.aws import AwsDevice, AwsQuantumTask


class BraketBackend(SubmissionBackend):
    device_arn: str = "arn:aws:braket:us-east-1::device/qpu/quera/Aquila"

    def _convert_status_codes(self, braket_message: str) -> QuEraTaskStatusCode:
        match braket_message:
            case str("CREATED"):
                return QuEraTaskStatusCode.Created

            case str("RUNNING"):
                return QuEraTaskStatusCode.Running

            case str("COMPLETED"):
                return QuEraTaskStatusCode.Completed

            case str("FAILED"):
                return QuEraTaskStatusCode.Failed

            case str("CANCELLED"):
                return QuEraTaskStatusCode.Cancelled

            case _:
                raise ValueError(f"unexpected argument {braket_message}")

    def _convert_task_results(self, task: AwsQuantumTask) -> QuEraTaskResults:
        if task.status() == "COMPLETED":
            result = task.result()
            shot_outputs = []
            for measurement in result.measurements:
                shot_outputs.append(
                    QuEraShotResult(
                        shot_status=QuEraShotStatusCode.Completed,
                        pre_sequence=list(measurement.pre_sequence),
                        post_sequence=list(measurement.post_sequence),
                    )
                )

            return QuEraTaskResults(
                task_status=QuEraTaskStatusCode.Completed, shot_outputs=shot_outputs
            )
        else:
            return QuEraTaskResults(
                task_status=self._convert_status_codes(task.status()), shot_outputs=[]
            )

    @property
    def device(self) -> AwsDevice:
        return AwsDevice(self.device_arn)

    def submit_task(self, task_ir: BraketTaskSpecification) -> str:
        task = self.device.run(task_ir.program, shots=task_ir.nshots)
        return task.id

    def task_results(self, task_id: str) -> QuEraTaskResults:
        task = AwsQuantumTask(task_id)
        return self._convert_task_results(task)

    def cancel_task(self, task_id: str) -> None:
        AwsQuantumTask(task_id).cancel()

    def task_status(self, task_id: str) -> QuEraTaskStatusCode:
        task = AwsQuantumTask(task_id)
        return self._convert_status_codes(task.state)
