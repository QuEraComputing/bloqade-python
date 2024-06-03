"""
This module contains the definition and serialization logic for the QuEraTask class, 
which represents a task to be run on a quantum computing backend. The QuEraTask class 
handles task submission, validation, status checking, and result fetching. The module 
also includes serialization and deserialization functions for the QuEraTask class, 
enabling tasks to be easily saved and loaded.
"""

import warnings
from dataclasses import dataclass, field
from bloqade.serialize import Serializer
from bloqade.submission.mock import MockBackend
from bloqade.task.base import Geometry, RemoteTask

from bloqade.submission.base import ValidationError
from bloqade.submission.ir.task_results import QuEraTaskResults, QuEraTaskStatusCode
from bloqade.submission.ir.task_specification import QuEraTaskSpecification
from bloqade.submission.ir.parallel import ParallelDecoder
from bloqade.submission.quera import QuEraBackend
from bloqade.builder.base import ParamType

from beartype.typing import Dict, Optional, Union, Any


@dataclass
@Serializer.register
class QuEraTask(RemoteTask):
    """
    Represents a task to be run on a quantum computing backend.

    Attributes:
        task_id (Optional[str]): The ID of the task.
        backend (Union[QuEraBackend, MockBackend]): The backend where the task is executed.
        task_ir (QuEraTaskSpecification): The task specification.
        metadata (Dict[str, ParamType]): Metadata associated with the task.
        parallel_decoder (Optional[ParallelDecoder]): Parallel decoder associated with the task.
        task_result_ir (QuEraTaskResults): The task result status.
    """

    task_id: Optional[str]
    backend: Union[QuEraBackend, MockBackend]
    task_ir: QuEraTaskSpecification
    metadata: Dict[str, ParamType]
    parallel_decoder: Optional[ParallelDecoder] = None
    task_result_ir: QuEraTaskResults = field(
        default_factory=lambda: QuEraTaskResults(
            task_status=QuEraTaskStatusCode.Unsubmitted
        )
    )

    def submit(self, force: bool = False) -> "QuEraTask":
        """
        Submits the task to the backend.

        Args:
            force (bool): If True, force submission even if the task is already submitted.

        Returns:
            QuEraTask: The submitted task.

        Raises:
            ValueError: If the task is already submitted and force is False.
        """
        if not force:
            if self.task_id is not None:
                raise ValueError(f"The task is already submitted with {self.task_id}")

        self.task_id = self.backend.submit_task(self.task_ir)
        self.task_result_ir = QuEraTaskResults(task_status=QuEraTaskStatusCode.Enqueued)

        return self

    def validate(self) -> str:
        """
        Validates the task specification against the backend.

        Returns:
            str: An empty string if validation is successful,otherwise the validation error message.
        """
        try:
            self.backend.validate_task(self.task_ir)
        except ValidationError as e:
            return str(e)

        return ""

    def fetch(self) -> "QuEraTask":
        """
        Fetches the task results if the task is completed.

        Returns:
            QuEraTask: The task with updated results.

        Raises:
            ValueError: If the task status is unsubmitted.
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

    def pull(self) -> "QuEraTask":
        """
        Blocks execution until task is in a stopped state, e.g. Completed, Cancelled, Failed, etc.

        Returns:
            QuEraTask: The task with updated results.

        Raises:
            ValueError: If the task ID is not found.
        """
        if self.task_id is None:
            raise ValueError("Task ID not found.")

        self.task_result_ir = self.backend.task_results(self.task_id)

        return self

    def result(self) -> QuEraTaskResults:
        """
        Retrieves the task results, blocking if necessary.

        Returns:
            QuEraTaskResults: The results of the task.
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
        Gets the current status of the task.

        Returns:
            QuEraTaskStatusCode: The status of the task.
        """
        if self.task_id is None:
            return QuEraTaskStatusCode.Unsubmitted

        return self.backend.task_status(self.task_id)

    def cancel(self) -> None:
        """
        Cancels the task if it is already submitted.

        Raises:
            UserWarning: If the task ID is not found.
        """
        if self.task_id is None:
            warnings.warn("Cannot cancel task, missing task id.")
            return

        self.backend.cancel_task(self.task_id)

    @property
    def nshots(self):
        """
        Returns the number of shots for the task.

        Returns:
            int: The number of shots.
        """
        return self.task_ir.nshots

    def _geometry(self) -> Geometry:
        """
        Retrieves the geometry of the task.

        Returns:
            Geometry: The geometry of the task.
        """
        return Geometry(
            sites=self.task_ir.lattice.sites,
            filling=self.task_ir.lattice.filling,
            parallel_decoder=self.parallel_decoder,
        )

    def _result_exists(self) -> bool:
        """
        Checks if the task result exists and is completed.

        Returns:
            bool: True if the task result exists and is completed, False otherwise.
        """
        if self.task_result_ir is None:
            return False
        else:
            if self.task_result_ir.task_status in [
                QuEraTaskStatusCode.Completed,
                QuEraTaskStatusCode.Partial,
            ]:
                return True
            else:
                return False


@QuEraTask.set_serializer
def _serialze(obj: QuEraTask) -> Dict[str, ParamType]:
    """
    Serializes the QuEraTask object.

    Args:
        obj (QuEraTask): The QuEraTask object to serialize.

    Returns:
        Dict[str, ParamType]: The serialized QuEraTask object.
    """
    return {
        "task_id": obj.task_id if obj.task_id is not None else None,
        "task_ir": obj.task_ir.dict(by_alias=True, exclude_none=True),
        "metadata": obj.metadata,
        "backend": {
            f"{obj.backend.__class__.__name__}": obj.backend.dict(
                exclude=set(["access_key", "secret_key", "session_token"])
            )
        },
        "parallel_decoder": (
            obj.parallel_decoder.dict() if obj.parallel_decoder else None
        ),
        "task_result_ir": obj.task_result_ir.dict() if obj.task_result_ir else None,
    }


@QuEraTask.set_deserializer
def _deserializer(d: Dict[str, Any]) -> QuEraTask:
    """
    Deserializes a dictionary into a QuEraTask object.

    Args:
        d (Dict[str, Any]): The dictionary to deserialize.

    Returns:
        QuEraTask: The deserialized QuEraTask object.
    """
    d["task_ir"] = QuEraTaskSpecification(**d["task_ir"])
    d["task_result_ir"] = (
        QuEraTaskResults(**d["task_result_ir"]) if d["task_result_ir"] else None
    )
    d["backend"] = (
        QuEraBackend(**d["backend"]["QuEraBackend"])
        if "QuEraBackend" in d["backend"]
        else MockBackend(**d["backend"]["MockBackend"])
    )
    d["parallel_decoder"] = (
        ParallelDecoder(**d["parallel_decoder"]) if d["parallel_decoder"] else None
    )
    return QuEraTask(**d)
