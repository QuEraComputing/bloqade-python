"""
Module for managing Braket tasks in the bloqade framework.

This module defines the BraketTask class, which represents a task that can be submitted
to a Braket backend. It includes methods for task submission, validation, fetching results,
checking status, and cancellation. Additionally, serialization and deserialization
functions are provided for the BraketTask class.
"""

import warnings
from dataclasses import dataclass, field
from beartype.typing import Dict, Optional, Any

from bloqade.builder.base import ParamType
from bloqade.serialize import Serializer
from bloqade.submission.ir.parallel import ParallelDecoder
from bloqade.task.base import Geometry, RemoteTask
from bloqade.submission.ir.task_specification import QuEraTaskSpecification
from bloqade.submission.braket import BraketBackend

from bloqade.submission.base import ValidationError
from bloqade.submission.ir.task_results import QuEraTaskResults, QuEraTaskStatusCode


## keep the old conversion for now,
## we will remove conversion btwn QuEraTask <-> BraketTask,
## and specialize/dispatching here.
@dataclass
@Serializer.register
class BraketTask(RemoteTask):
    """
    Represents a Braket Task which can be submitted to a Braket backend.

    Attributes:
        task_id (Optional[str]): The ID of the task.
        backend (BraketBackend): The backend to which the task is submitted.
        task_ir (QuEraTaskSpecification): The task specification.
        metadata (Dict[str, ParamType]): Metadata associated with the task.
        parallel_decoder (Optional[ParallelDecoder]): Parallel decoder for the task.
        task_result_ir (QuEraTaskResults): The result of the task.
    """

    task_id: Optional[str]
    backend: BraketBackend
    task_ir: QuEraTaskSpecification
    metadata: Dict[str, ParamType]
    parallel_decoder: Optional[ParallelDecoder] = None
    task_result_ir: QuEraTaskResults = field(
        default_factory=lambda: QuEraTaskResults(
            task_status=QuEraTaskStatusCode.Unsubmitted
        )
    )

    def submit(self, force: bool = False) -> "BraketTask":
        """
        Submits the task to the backend.

        Args:
            force (bool): Whether to force submission even if the task is already submitted.

        Returns:
            BraketTask: The current task instance.

        Raises:
            ValueError: If the task is already submitted and force is False.
        """
        if not force:
            if self.task_id is not None:
                raise ValueError(f"the task is already submitted with {self.task_id}")
        self.task_id = self.backend.submit_task(self.task_ir)

        self.task_result_ir = QuEraTaskResults(task_status=QuEraTaskStatusCode.Enqueued)

        return self

    def validate(self) -> str:
        """
        Validates the task specification.

        Returns:
            str: An empty string if validation is successful,otherwise the validation error message.
        """
        try:
            self.backend.validate_task(self.task_ir)
        except ValidationError as e:
            return str(e)

        return ""

    def fetch(self) -> "BraketTask":
        """
        Fetches the task results if the task is completed.

        Returns:
            BraketTask: The current task instance.

        Raises:
            ValueError: If the task is not yet submitted.
        """
        if self.task_result_ir.task_status is QuEraTaskStatusCode.Unsubmitted:
            raise ValueError("Task ID not found.")

        if self.task_result_ir.task_status in [
            QuEraTaskStatusCode.Completed,
            QuEraTaskStatusCode.Partial,
            QuEraTaskStatusCode.Failed,
            QuEraTaskStatusCode.Unaccepted,
            QuEraTaskStatusCode.Cancelled,
        ]:
            return self

        status = self.status()
        if status in [QuEraTaskStatusCode.Completed, QuEraTaskStatusCode.Partial]:
            self.task_result_ir = self.backend.task_results(self.task_id)
        else:
            self.task_result_ir = QuEraTaskResults(task_status=status)

        return self

    def pull(self) -> "BraketTask":
        """
        Forces pulling the task results.

        Returns:
            BraketTask: The current task instance.

        Raises:
            ValueError: If the task ID is not found.
        """
        if self.task_id is None:
            raise ValueError("Task ID not found.")

        self.task_result_ir = self.backend.task_results(self.task_id)

        return self

    def result(self) -> QuEraTaskResults:
        """
        Gets the task results, blocking until results are available.

        Returns:
            QuEraTaskResults: The task results.
        """
        if self.task_result_ir is None:
            pass
        else:
            if (
                self.task_id is not None
                and self.task_result_ir.task_status != QuEraTaskStatusCode.Completed
            ):
                self.pull()

        return self.task_result_ir

    def status(self) -> QuEraTaskStatusCode:
        """
        Gets the status of the task.

        Returns:
            QuEraTaskStatusCode: The status of the task.
        """
        if self.task_id is None:
            return QuEraTaskStatusCode.Unsubmitted

        return self.backend.task_status(self.task_id)

    def cancel(self) -> None:
        """
        Cancels the task if it is currently submitted.

        Returns:
            None

        Raises:
            Warning: If the task ID is not found.
        """
        if self.task_id is None:
            warnings.warn("Cannot cancel task, missing task id.")
            return

        self.backend.cancel_task(self.task_id)

    @property
    def nshots(self):
        """
        Gets the number of shots specified for the task.

        Returns:
            int: The number of shots.
        """
        return self.task_ir.nshots

    def _geometry(self) -> Geometry:
        """
        Gets the geometry of the task lattice.

        Returns:
            Geometry: The geometry of the task lattice.
        """
        return Geometry(
            sites=self.task_ir.lattice.sites,
            filling=self.task_ir.lattice.filling,
            parallel_decoder=self.parallel_decoder,
        )

    def _result_exists(self) -> bool:
        """
        Checks if the task results exist.

        Returns:
            bool: True if the task results exist and are completed, otherwise False.
        """
        if self.task_result_ir is None:
            return False
        else:
            if self.task_result_ir.task_status == QuEraTaskStatusCode.Completed:
                return True
            else:
                return False


@BraketTask.set_serializer
def _serialize(obj: BraketTask) -> Dict[str, Any]:
    """
    Serializes the BraketTask instance to a dictionary.

    Args:
        obj (BraketTask): The task instance to serialize.

    Returns:
        Dict[str, Any]: The serialized dictionary representation of the task.
    """
    return {
        "task_id": obj.task_id,
        "backend": obj.backend.dict(),
        "task_ir": obj.task_ir.dict(exclude_none=True, by_alias=True),
        "metadata": obj.metadata,
        "parallel_decoder": (
            obj.parallel_decoder.dict() if obj.parallel_decoder else None
        ),
        "task_result_ir": obj.task_result_ir.dict() if obj.task_result_ir else None,
    }


@BraketTask.set_deserializer
def _deserialize(d: Dict[str, Any]) -> BraketTask:
    """
    Deserializes a dictionary to a BraketTask instance.

    Args:
        d (Dict[str, Any]): The dictionary to deserialize.

    Returns:
        BraketTask: The deserialized task instance.
    """
    d["backend"] = BraketBackend(**d["backend"])
    d["task_ir"] = QuEraTaskSpecification(**d["task_ir"])
    d["parallel_decoder"] = (
        ParallelDecoder(**d["parallel_decoder"]) if d["parallel_decoder"] else None
    )
    d["task_result_ir"] = (
        QuEraTaskResults(**d["task_result_ir"]) if d["task_result_ir"] else None
    )
    return BraketTask(**d)
