"""Module for `BraketBackend` which represents the functionalities
needed for executing programs on Braket backend"""

import warnings
from bloqade.submission.base import SubmissionBackend
from bloqade.submission.ir.braket import (
    from_braket_task_results,
    from_braket_status_codes,
    to_braket_task,
    to_quera_capabilities,
)
from bloqade.submission.ir.capabilities import QuEraCapabilities
from bloqade.submission.ir.task_results import (
    QuEraTaskStatusCode,
    QuEraTaskResults,
)
from bloqade.submission.ir.task_specification import QuEraTaskSpecification
from braket.aws import AwsDevice, AwsQuantumTask
from beartype.typing import Optional
from pydantic.v1 import PrivateAttr
import bloqade


class BraketBackend(SubmissionBackend):
    """Class representing the functionalities needed for executing
    programs on Braket backend.

    Attributes:
    device_arn(str): AWS arn for quantum program execution.
        Defaults to `"arn:aws:braket:us-east-1::device/qpu/quera/Aquila"`
    """

    device_arn: str = "arn:aws:braket:us-east-1::device/qpu/quera/Aquila"
    _device: Optional[AwsDevice] = PrivateAttr(default=None)

    @property
    def device(self) -> AwsDevice:
        """Amazon Braket implementation of a device. Use this class to retrieve
        the latest metadata about the device and to run a quantum task on the device.
        """
        if self._device is None:
            self._device = AwsDevice(self.device_arn)
            user_agent = f"Bloqade/{bloqade.__version__}"
            self._device.aws_session.add_braket_user_agent(user_agent)

        return self._device

    def get_capabilities(self, use_experimental: bool = False) -> QuEraCapabilities:
        """Get the capabilities of the QuEra backend.
        Args:
        use_experimental (bool): Whether to use experimental capabilities of
            the backend system. Defaults to `False`.
        Returns:
        An object to the type `QuEraCapabilities`, representing the capabilities
        of the selected QuEra backend.
        """
        from botocore.exceptions import BotoCoreError, ClientError

        if use_experimental:
            return super().get_capabilities(use_experimental)

        try:
            return to_quera_capabilities(self.device.properties.paradigm)
        except BotoCoreError:
            warnings.warn(
                "Could not retrieve device capabilities from braket API. "
                "Using local capabilities file for Aquila."
            )
        except ClientError:
            warnings.warn(
                "Could not retrieve device capabilities from braket API. "
                "Using local capabilities file for Aquila."
            )

        return super().get_capabilities()

    def submit_task(self, task_ir: QuEraTaskSpecification) -> str:
        """Submit the task to the Braket backend. It converts task
        IR(Intermediate Representation) of the QuEra system to suitable format
        accepted by Braket.

        Args:
        task_ir (QuEraTaskSpecification): task IR(Intermediate Represetation)
        suitable for QuEra backend. It will be converted to appropriate
        IR(Intermediate Represetation) accepted by Braket backend

        Returns:
        Task id as a result of executing IR(Intermediate Represetation)
        on the Braket backend.
        """
        shots, ahs_program = to_braket_task(task_ir)
        task = self.device.run(ahs_program, shots=shots)
        return task.id

    def task_results(self, task_id: str) -> QuEraTaskResults:
        """Get the result of the task by using the task id of Braket backend.

        Args:
        task_id (str): task id after executing program on the Braket backend.

        Returns:
        Task result of the type `QuEraTaskResults` from task id
        of the Braket backend.
        """
        return from_braket_task_results(AwsQuantumTask(task_id).result())

    def cancel_task(self, task_id: str) -> None:
        """Cancels the task submitted to the Braket backend.
        Args:
        task_id (str): task id after executing program on the Bracket backend.
        """
        AwsQuantumTask(task_id).cancel()

    def task_status(self, task_id: str) -> QuEraTaskStatusCode:
        """Get the status of the task submitted by using the task id of Braket backend.

        Args:
        task_id (str): task id after executing program on the Braket backend.

        Returns:
        Task status of the type `QuEraTaskStatusCode` by using the task id
        of the Braket backend.
        """
        return from_braket_status_codes(AwsQuantumTask(task_id).state())

    def validate_task(self, task_ir: QuEraTaskSpecification):
        """Validates the task submitted to the QuEra backend.

        Args:
        task_ir (QuEraTaskSpecification): task IR(Intermediate Represetation)
        suitable for QuEra backend. It will be converted to appropriate
        IR(Intermediate Representation) accepted by Braket backend.

        Raises:
        ValidationError: For tasks that fail validation.

        Notes:
        Currently, it's a no-op.
        """
        pass

    # def validate_task(self, task_ir: QuEraTaskSpecification):
    #     try:
    #         task_id = self.submit_task(task_ir)
    #     except Exception as e:
    #         if "ValidationException" in str(e) and "validation error" in str(e):
    #             raise ValidationError(str(e))
    #         else:
    #             raise e

    #     # don't want the task to actually run
    #     try:
    #         self.cancel_task(task_id)
    #     except Exception as e:
    #         return
