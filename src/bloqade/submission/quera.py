"""Module to host QueraBackend class that hosts different functionalities
representing the backend of the QuEra system(s)."""

from pydantic.v1 import PrivateAttr
from bloqade.submission.base import SubmissionBackend, ValidationError
from bloqade.submission.ir.task_specification import (
    QuEraTaskSpecification,
)
from bloqade.submission.ir.capabilities import QuEraCapabilities
from bloqade.submission.ir.task_results import (
    QuEraTaskResults,
    QuEraTaskStatusCode,
)
from typing import Optional


class QuEraBackend(SubmissionBackend):
    """Class to represent QuEra backend.

    Attributes:
        api_hostname (str): API of the host.
        qpu_id (str): QPU id.
        api_stage (str): API version. Defaults to "v0"
        virtual_queue (Optional[str]) = Virtual queue in QuEra backend.
            Defaults to `None`.
        proxy (Optional[str]): proxy for Quera backend. Defaults to `None`.
        # Sigv4Request arguments
        region (Optional[str]): Sigv4Request argument for region of QuEra backend.
            Defaults to `None`.
        access_key (Optional[str]): Sigv4Request argument representing the access
            key required to access QuEra backend. Defaults to `None`.
        secret_key (Optional[str]): Sigv4Request argument representing the secret
            key required to access QuEra backend. Defaults to `None`.
        session_token (Optional[str]): Sigv4Request argument representing the session
            token of the QuEra backend. Defaults to `None`.
        session_expires (Optional[int]) = Sigv4Request argument representing the
            expiration timestamp for the session on QuEra backend. Defaults to `None`.
        role_arn (Optional[str]) = Role of the user accessing QuEra backend.
            Defaults to `None`.
        role_session_name (Optional[str]) = Role session name for QuEra backend.
            Defaults to `None`.
        profile (Optional[str]) = User profile for QuEra backend.
            Defaults to `None`.
    """

    api_hostname: str
    qpu_id: str
    api_stage: str = "v0"
    virtual_queue: Optional[str] = None
    proxy: Optional[str] = None
    # Sigv4Request arguments
    region: Optional[str] = None
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    session_token: Optional[str] = None
    session_expires: Optional[int] = None
    role_arn: Optional[str] = None
    role_session_name: Optional[str] = None
    profile: Optional[str] = None
    _queue_api: Optional[object] = PrivateAttr(None)

    @property
    def queue_api(self):
        if self._queue_api is None:
            try:
                from qcs.api_client.api import QueueApi
            except ImportError:
                raise RuntimeError("Must install QuEra-QCS-client to use QuEra Cloud")

            kwargs = {k: v for k, v in self.__dict__.items() if v is not None}
            self._queue_api = QueueApi(**kwargs)

        return self._queue_api

    def get_capabilities(self, use_experimental: bool = False) -> QuEraCapabilities:
        """Get the capabilities of the QuEra backend.

        Args:
            use_experimental (bool): Whether to use experimental capabilities of
                the QuEra system. Defaults to `False`.

        Returns:
            capabilities (QuEraCapabilities): capabilities of the selected
                QuEra backend.
        """
        try:
            return QuEraCapabilities(**self.queue_api.get_capabilities())
        except BaseException:
            return super().get_capabilities(use_experimental)

    def submit_task(self, task_ir: QuEraTaskSpecification) -> str:
        """Submit the task to the QuEra backend.

        Args:
            task_ir (QuEraTaskSpecification): task IR to be
                executed on the QuEra backend.

        Returns:
            task_id (str): Task id as a result of executing
                IR on the QuEra backend.
        """
        return self.queue_api.submit_task(
            task_ir.json(by_alias=True, exclude_none=True, exclude_unset=True)
        )

    def task_results(self, task_id: str) -> QuEraTaskResults:
        """Get the status of the task submitted to the QuEra backend
        by using the task id.

        Args:
            task_id (str): task id after executing program on the QuEra backend.

        Returns:
            task_result (QuEraTaskResults):
                Final result of the task by using the task id.
        """
        return QuEraTaskResults(**self.queue_api.poll_task_results(task_id))

    def cancel_task(self, task_id: str):
        """Cancels the task submitted to the QuEra backend.

        Args:
            task_id (str): task id after executing program on the QuEra backend.
        """
        self.queue_api.cancel_task_in_queue(task_id)

    def task_status(self, task_id: str) -> QuEraTaskStatusCode:
        """Get the status of the task submitted to the QuEra backend
        by using the task id.

        Args:
            task_id (str): task id after executing program on the QuEra backend.

        Returns:
            task_status (QuEraTaskStatusCode): status of the task by using the task id.
        """
        return_body = self.queue_api.get_task_status_in_queue(task_id)
        return QuEraTaskStatusCode(return_body)

    def validate_task(self, task_ir: QuEraTaskSpecification):
        """Validates the task submitted to the QuEra backend.

        Args:
            task_ir (QuEraTaskSpecification): task IR to be
                executed on the QuEra backend.

        Raises:
            ValidationError: For tasks that fail validation.
        """
        try:
            self.queue_api.validate_task(
                task_ir.json(by_alias=True, exclude_none=True, exclude_unset=True)
            )
        except self.queue_api.ValidationError as e:
            raise ValidationError(str(e))

    def update_credential(
        self, access_key: str = None, secret_key: str = None, session_token: str = None
    ):
        """Update the credentials

        Args:
            access_key (Optional[str]): Sigv4Request argument representing the access
                key required to access QuEra backend. Defaults to `None`
            secret_key (Optional[str]): Sigv4Request argument representing the secret
                key required to access QuEra backend. Defaults to `None`
            session_token (Optional[str]): Sigv4Request argument representing the
                session token of the QuEra backend. Defaults to `None`
        """
        if secret_key is not None:
            self.secret_key = secret_key
        if access_key is not None:
            self.access_key = access_key
        if session_token is not None:
            self.session_token = session_token
