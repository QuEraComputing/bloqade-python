from bloqade.builder.base import ParamType
from .base import LocalTask
from bloqade.submission.ir.task_results import QuEraTaskResults
from bloqade.submission.ir.braket import (
    from_braket_task_results,
    BraketTaskSpecification,
)
from bloqade.task.base import Geometry
from braket.devices import LocalSimulator
from typing import Dict, Optional
from pydantic.dataclasses import dataclass

## keep the old conversion for now,
## we will remove conversion btwn QuEraTask <-> BraketTask,
## and specialize/dispatching here.


@dataclass
class BraketEmulatorTask(LocalTask):
    task_ir: BraketTaskSpecification
    metadata: Dict[str, ParamType]
    task_result_ir: Optional[QuEraTaskResults] = None

    def _geometry(self) -> Geometry:
        return Geometry(
            sites=self.task_data.task_ir.program.setup.ahs_register.sites,
            filling=self.task_data.task_ir.program.setup.ahs_register.filling,
        )

    def run(self, **kwargs) -> None:
        aws_task = LocalSimulator("braket_ahs").run(
            self.task_data.task_ir.program,
            shots=self.task_data.task_ir.nshots,
            **kwargs,
        )
        self.task_result_ir = from_braket_task_results(aws_task.result())

    def result(self):
        if self.task_result_ir is None:
            raise ValueError("Braket simulator job haven't submit yet.")

        return self.task_result_ir
