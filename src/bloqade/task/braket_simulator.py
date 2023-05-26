from pydantic import BaseModel
from braket.devices import LocalSimulator

from bloqade.submission.ir.braket import (
    BraketTaskSpecification,
    from_braket_task_results,
)
from bloqade.submission.ir.task_results import (
    QuEraTaskResults,
    QuEraTaskStatusCode,
)
from bloqade.task import Task, TaskFuture


class BraketEmulatorTask(BaseModel, Task):
    braket_emulator_task_ir: BraketTaskSpecification

    @property
    def device(self):
        return LocalSimulator("default_ahs")

    def submit(self) -> "BraketEmulatorTaskFuture":
        aws_task = self.device.run(self.task_ir.program, shots=self.task_ir.nshots)

        return BraketEmulatorTaskFuture(
            task_results_ir=from_braket_task_results(aws_task.result())
        )


class BraketEmulatorTaskFuture(BaseModel, TaskFuture):
    task_results_ir: QuEraTaskResults

    def fetch(self, cache_results=False) -> QuEraTaskResults:
        return self.task_results_ir

    def status(self) -> QuEraTaskStatusCode:
        return QuEraTaskStatusCode.Completed

    def cancel(self) -> None:
        pass
