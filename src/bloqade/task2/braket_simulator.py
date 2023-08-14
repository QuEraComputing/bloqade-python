from .base import Task, JSONInterface
from bloqade.submission.braket import BraketBackend
from bloqade.submission.ir.task_results import QuEraTaskResults
from bloqade.submission.ir.braket import (
    BraketTaskSpecification,
    from_braket_task_results,
)
from bloqade.task2.base import Geometry
from braket.devices import LocalSimulator


## keep the old conversion for now,
## we will remove conversion btwn QuEraTask <-> BraketTask,
## and specialize/dispatching here.
class BraketEmulatorTask(Task, JSONInterface):
    task_ir: BraketTaskSpecification  # task_ir contain result/statevec
    task_result_ir: QuEraTaskResults

    def __init__(
        self,
        task_ir: BraketTaskSpecification,
        backend: BraketBackend = None,
        **kwargs,
    ):
        super().__init__(
            task_id=None,
        )
        self.task_ir = task_ir
        self.backend = backend

    def _geometry(self) -> Geometry:
        return Geometry(
            sites=self.task_ir.program.setup.ahs_register.sites,
            filling=self.task_ir.program.setup.ahs_register.filling,
        )

    def submit(self, **kwargs) -> None:
        aws_task = LocalSimulator("braket_ahs").run(
            self.task_ir.program, shots=self.task_ir.nshots, **kwargs
        )
        self.task_result_ir = from_braket_task_results(aws_task.result())

    def result(self) -> QuEraTaskResults:
        if self.task_result_ir is None:
            raise ValueError("Braket simulator job haven't submit yet.")

        return self.task_result_ir
