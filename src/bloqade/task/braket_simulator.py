"""
This module defines the BraketEmulatorTask class which integrates with the AWS Braket LocalSimulator 
to run and manage quantum tasks, and serialize/deserialize task information.
"""

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
    """
    Represents a quantum task that runs on the AWS Braket LocalSimulator.

    Attributes:
        task_ir (BraketTaskSpecification): The task specification for the Braket simulator.
        metadata (Dict[str, ParamType]): Metadata related to the task.
        task_result_ir (Optional[QuEraTaskResults]): The results of the task, if available.
    """

    task_ir: BraketTaskSpecification
    metadata: Dict[str, ParamType]
    task_result_ir: Optional[QuEraTaskResults] = None

    def _geometry(self) -> Geometry:
        """
        Constructs and returns the Geometry of the task based on the AHS register setup.

        Returns:
            Geometry: The geometric setup of the task.
        """
        return Geometry(
            sites=self.task_ir.program.setup.ahs_register.sites,
            filling=self.task_ir.program.setup.ahs_register.filling,
        )

    def run(self, **kwargs) -> "BraketEmulatorTask":
        """
        Runs the task on the Braket LocalSimulator.

        Args:
            **kwargs: Additional arguments for the simulator run method.

        Returns:
            BraketEmulatorTask: The current instance with the task results updated.
        
        Example:
            >>> task_spec = BraketTaskSpecification(...)  # Task specification setup
            >>> metadata = {"param1": value1, "param2": value2}
            >>> task = BraketEmulatorTask(task_ir=task_spec, metadata=metadata)
            >>> task.run(shots=1000)
            >>> results = task.result()
        """
        aws_task = LocalSimulator("braket_ahs").run(
            self.task_ir.program,
            shots=self.task_ir.nshots,
            **kwargs,
        )
        self.task_result_ir = from_braket_task_results(aws_task.result())
        return self

    def result(self) -> QuEraTaskResults:
        """
        Retrieves the results of the task.

        Returns:
            QuEraTaskResults: The results of the task.

        Raises:
            ValueError: If the task has not been submitted yet.
        
        Example:
            >>> task_spec = BraketTaskSpecification(...)  # Task specification setup
            >>> metadata = {"param1": value1, "param2": value2}
            >>> task = BraketEmulatorTask(task_ir=task_spec, metadata=metadata)
            >>> task.run(shots=1000)
            >>> results = task.result()
        """
        if self.task_result_ir is None:
            raise ValueError("Braket simulator job hasn't been submitted yet.")

        return self.task_result_ir

    @property
    def nshots(self) -> int:
        """
        Returns the number of shots for the task.

        Returns:
            int: The number of shots.

        Example:
            >>> task_spec = BraketTaskSpecification(...)  # Task specification setup
            >>> metadata = {"param1": value1, "param2": value2}
            >>> task = BraketEmulatorTask(task_ir=task_spec, metadata=metadata)
            >>> num_shots = task.nshots
        """
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
