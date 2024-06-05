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

        Example:
            >>> backend = BraketBackend(...)  # Create a backend instance
            >>> task_ir = QuEraTaskSpecification(...)  # Create a task specification
            >>> metadata = {"key": "value"}  # Metadata for the task
            >>> braket_task = BraketTask(
            ...     task_id=None,
            ...     backend=backend,
            ...     task_ir=task_ir,
            ...     metadata=metadata,
            ... )
            >>> braket_task.submit()
            >>> print(f"Task submitted with ID: {braket_task.task_id}")
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
            str: An empty string if validation is successful, otherwise the validation error message.

        Example:
            >>> validation_error = braket_task.validate()
            >>> if validation_error:
            ...     print(f"Validation Error: {validation_error}")
            ... else:
            ...     print("Task is valid.")
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

        Example:
            >>> try:
            ...     braket_task.fetch()
            ...     results = braket_task.result()
            ...     print(f"Task results: {results}")
            ... except ValueError as e:
            ...     print(e)
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

        Example:
            >>> try:
            ...     braket_task.pull()
            ...     results = braket_task.result()
            ...     print(f"Task results: {results}")
            ... except ValueError as e:
            ...     print(e)
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

        Example:
            >>> results = braket_task.result()
            >>> print(f"Task results: {results}")
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

        Example:
            >>> status = braket_task.status()
            >>> print(f"Task status: {status.name}")
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

        Example:
            >>> try:
            ...     braket_task.cancel()
            ...     print("Task cancelled.")
            ... except Warning as w:
            ...     print(w)
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

        Example:
            >>> print(f"Number of shots: {braket_task.nshots}")
        """
        return self.task_ir.nshots

    def _geometry(self) -> Geometry:
        """
        Gets the geometry of the task lattice.

        Returns:
            Geometry: The geometry of the task lattice.

        Example:
            >>> geometry = braket_task._geometry()
            >>> print(f"Task geometry: {geometry}")
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

        Example:
            >>> result_exists = braket_task._result_exists()
            >>> print(f"Result exists: {result_exists}")
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
    d["backend"] = BraketBackend(**d["backend"])
    d["task_ir"] = QuEraTaskSpecification(**d["task_ir"])
    d["parallel_decoder"] = (
        ParallelDecoder(**d["parallel_decoder"]) if d["parallel_decoder"] else None
    )
    d["task_result_ir"] = (
        QuEraTaskResults(**d["task_result_ir"]) if d["task_result_ir"] else None
    )
    return BraketTask(**d)
