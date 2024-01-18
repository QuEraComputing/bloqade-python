from bloqade.serialize import Serializer
from bloqade.builder.base import ParamType
from .base import LocalTask
from bloqade.submission.ir.task_results import QuEraTaskResults
from bloqade.submission.ir.braket import (
    from_braket_task_results,
    BraketTaskSpecification,
)
from bloqade.task.base import Geometry
from braket.devices import LocalSimulator
from beartype.typing import Dict, Optional, Any
from dataclasses import dataclass

## keep the old conversion for now,
## we will remove conversion btwn QuEraTask <-> BraketTask,
## and specialize/dispatching here.


@dataclass
@Serializer.register
class BraketEmulatorTask(LocalTask):
    task_ir: BraketTaskSpecification
    metadata: Dict[str, ParamType]
    task_result_ir: Optional[QuEraTaskResults] = None

    def _geometry(self) -> Geometry:
        return Geometry(
            sites=self.task_ir.program.setup.ahs_register.sites,
            filling=self.task_ir.program.setup.ahs_register.filling,
        )

    def run(self, **kwargs) -> "BraketEmulatorTask":
        aws_task = LocalSimulator("braket_ahs").run(
            self.task_ir.program,
            shots=self.task_ir.nshots,
            **kwargs,
        )
        self.task_result_ir = from_braket_task_results(aws_task.result())
        return self

    def result(self):
        if self.task_result_ir is None:
            raise ValueError("Braket simulator job haven't submit yet.")

        return self.task_result_ir

    @property
    def nshots(self):
        return self.task_ir.nshots


@BraketEmulatorTask.set_serializer
def _serialize(obj: BraketEmulatorTask) -> Dict[str, Any]:
    return {
        "task_ir": obj.task_ir.dict(),
        "metadata": obj.metadata,
        "task_result_ir": obj.task_result_ir.dict() if obj.task_result_ir else None,
    }


@BraketEmulatorTask.set_deserializer
def _serializer(d: Dict[str, Any]) -> BraketEmulatorTask:
    d["task_ir"] = BraketTaskSpecification(**d["task_ir"])
    d["task_result_ir"] = (
        QuEraTaskResults(**d["task_result_ir"]) if d["task_result_ir"] else None
    )
    return BraketEmulatorTask(**d)
