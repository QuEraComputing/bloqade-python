import json
import logging
from types import NoneType
import uuid
from typing import Optional, Union
import requests
from aws_requests_auth.boto_utils import BotoAWSRequestsAuth


class QueueApi:
    """Simple interface to the QCS task API.

    Example (replace URL, QPU ID, and tentant ID with correct values):
    >>> task = r'{"nshots":100,"lattice":{"sites":[[0,0]],"filling":[1]},'
    ...       r'"effective_hamiltonian":{"rydberg":{"detuning":{"global":{"values":[0,0]
        ,"times":[0,0.000001]}},'
    ...       r'"rabi_frequency_phase":{"global":{"values":[0,0],
    "times":[0,0.000001]}},'
    ...       r'"rabi_frequency_amplitude":{"global":{"values":[0,0],
        "times":[0,0.000001]}}}}}'
    To Use this class with API-Gateway:
    >>> from aws_requests_auth.boto_utils import BotoAWSRequestsAuth
    >>> auth = BotoAWSRequestsAuth(aws_host='XXX.execute-api.us-east-1.amazonaws.com',
                        aws_region='us-east-1',
                        aws_service='execute-api')
    >>> url = "https://XXX.execute-api.us-east-1.amazonaws.com/v0"
    >>> qpu_id = "qpu1-mock"
    >>> api = QueueApi(url,qpu_id,auth=auth)
    >>> print(api.is_ready_for_task())
    """

    bad_request = (
        "The request is invalid. This may indicate an error when parsing a parameter."
    )
    bad_submit_task_request = "The request is invalid. This may indicate an error when"
    "parsing a parameter, or an error when parsing or validating the request body. "
    "The response body may contain a JSON array with a list of validation errors."

    qpu_not_found = "The QPU targeted by the request does not exist, or the user \
making the request is not authorized to access the targeted QPU."

    qpu_or_task_not_found = "The QPU or task targeted by the request does not exist, \
or the user making the request is not authorized to access the targeted QPU or task."

    class QueueApiError(RuntimeError):
        pass

    class QpuBusyError(QueueApiError):
        pass

    class NotFound(QueueApiError):
        pass

    class InvalidRequestError(QueueApiError):
        pass

    class InvalidResponseError(QueueApiError):
        pass

    class ValidationError(QueueApiError):
        pass

    class AuthenticationError(QueueApiError):
        pass

    def __init__(
        self,
        uri: str,
        qpu_id: str,
        api_version="v0",
        auth: Optional[requests.auth.AuthBase] = None,
    ):
        """
        Create an instance of `QueueApi`.
        @param uri: Uri for the API endpoints.
        @param qpu_id: The QPU ID, for example `qpu1-mock`.
        @param api_version: Specify which version of the API to call from this object.
        @param auth: Authenetication object to so sigv4 signing. You can use
            aws-request-auth
        """
        uri_with_version = uri + f"/{api_version}"
        if auth is None:
            self.auth = BotoAWSRequestsAuth(
                aws_host=uri, aws_region="us-east-1", aws_service="execute-api"
            )
            creds = self.auth._refreshable_credentials.get_frozen_credentials()
            if creds is None:
                raise QueueApi.AuthenticationError(
                    "Missing local AWS Credentials needed to access Queue."
                )
        else:
            self.auth = auth

        self.base_url = "https://" + uri_with_version
        self.qpu_id = qpu_id
        self.logger = logging.getLogger(self.__class__.__name__)

    @staticmethod
    def _result_as_json(result: requests.Response) -> dict:
        content_type = result.headers["Content-Type"]
        if content_type != "application/json":
            raise QueueApi.InvalidResponseError(
                f"Expected Content-Type application/json, but {content_type} found."
            )

        if len(result.content) == 0:
            return {}

        return json.loads(result.content)

    def _generate_headers(
        self, base: dict = {"Content-Type": "application/json"}
    ) -> dict:
        return base

    def _get_path(self, *path_list: str):
        return "/".join((self.base_url, self.qpu_id) + path_list)

    def post_task(self, content: Union[str, dict]) -> str:
        """
        Submit a task to the QPU via the task API.
        @param content: Task specification as a JSON string or dictionary.
        """
        url = self._get_path("queue", "task")
        self.logger.info(f'POSTing a task to "{url}".')
        headers = self._generate_headers()

        if type(content) == dict:
            content = json.dumps(content)

        result = requests.post(url, headers=headers, data=content, auth=self.auth)
        self.logger.debug(f"API return status {result.status_code}.")

        match result.status_code:
            case 201:
                message = "Successfully posted task."
                self.logger.warning(message)

            case 404:
                message = f"QPU {self.qpu_id} not found."
                self.logger.error(message)
                raise QueueApi.NotFound(message)

            case 400:
                message = (
                    "The request is invalid. This may indicate an error when"
                    "parsing a parameter."
                )
                self.logger.error(message)
                raise QueueApi.InvalidRequestError(message)

            case 403:
                message = "QPU return authentication error, check AWS credentials."
                self.logger.error(message)

            case _:
                message = f"QPU returned unhandled status {result.status_code}."
                self.logger.error(message)
                raise QueueApi.QueueApiError(message)

        result_json = QueueApi._result_as_json(result)

        try:
            task_id = result_json["task_id"]
            self.logger.info(f"QPU {self.qpu_id} accepted task with task id {task_id}.")
            return task_id
        except KeyError:
            raise QueueApi.InvalidResponseError('Response did not contain "task_id".')

    def get_capabilities(self) -> dict:
        """
        Request the QPU capabilities from the task API.
        @return: dictionary containing different fields for capabilities.
        """
        url = "/".join((self.base_url, self.qpu_id, "capabilities"))
        self.logger.info(f'GETting capabilities from  "{url}".')
        headers = self._generate_headers()
        result = requests.get(url, headers=headers, auth=self.auth)

        match result.status_code:
            case 200:
                message = "Successfully fetched capabilities."
                self.logger.error(message)

            case 404:
                message = f"QPU {self.qpu_id} not found."
                self.logger.error(message)
                raise QueueApi.NotFound(message)

            case 403:
                message = "QPU return authentication error, check AWS credentials."
                self.logger.error(message)
                raise QueueApi.AuthenticationError(message)

            case _:
                message = f"QPU returned unhandled status {result.status_code}."
                self.logger.error(message)
                raise QueueApi.QueueApiError(message)

        return QueueApi._result_as_json(result)

    def validate_task(self, content: Union[str, dict]) -> NoneType:
        url = "/".join(((self.base_url, self.qpu_id, "task", "validate")))
        self.logger.info(f'POSTing a task to "{url}".')
        headers = self._generate_headers()

        if type(content) == dict:
            content = json.dumps(content)

        result = requests.post(url, headers=headers, data=content, auth=self.auth)

        self.logger.debug(f"API return status {result.status_code}.")

        match result.status_code:
            case 200:
                message = "Task passed validation."
                self.logger.info(message)

            case 400:
                message = f"Task did not pass validation: {result.text}"
                self.logger.error(message)
                raise QueueApi.ValidationError(message)

            case 404:
                message = f"QPU {self.qpu_id} not found."
                self.logger.error(message)
                raise QueueApi.NotFound(message)

            case 403:
                message = "QPU return authentication error, check AWS credentials."
                self.logger.error(message)
                raise QueueApi.AuthenticationError(message)

            case _:
                message = f"QPU returned unhandled status {result.status_code}."
                self.logger.error(message)
                raise QueueApi.QueueApiError(message)

    def get_task_results(self, task_id: Union[str, uuid.UUID]) -> dict:
        """
        Return task results as given by API.
        @return: Parsed JSON of the task results.
        @param task_id: Task ID.
        """

        queue_status = self.get_task_status_in_queue(task_id)
        # TODO: Revisit this mapping when the queue API is
        #       has task result fetching build into the API
        match queue_status:  # overwrite the
            case "Created" | "Enqueued" | "Accepted":
                return {"task_status": "Created", "shot_outputs": []}
            case "Executing":
                return {"task_status": "Running", "shot_outputs": []}
            case "Failed" | "Cancelled":
                return {"task_status": queue_status, "shot_outputs": []}
            case "Unaccepted":
                raise QueueApi.ValidationError(
                    f"Task: {task_id} has validation error,"
                    " unable to fetch error message."
                )
            case "Completed":
                pass
            case _:
                raise QueueApi.QueueApiError(
                    f"Undocumented queue status: {queue_status}"
                )

        url = self._get_path("task", str(task_id), "results")
        self.logger.info(f'GETting task summary from  "{url}".')
        result = requests.get(url, headers=self._generate_headers(), auth=self.auth)
        self.logger.debug(f"API return status {result.status_code}.")

        match result.status_code:
            case 200:
                message = f"Successfully fetch task results for task_id {task_id}"
                self.logger.debug(message)

            case 400:
                message = QueueApi.bad_request
                self.logger.debug(message)
                raise QueueApi.InvalidRequestError(message)

            case 404:
                message = QueueApi.qpu_or_task_not_found
                self.logger.debug(message)
                raise QueueApi.NotFound(message)

            case 403:
                message = "QPU return authentication error, check AWS credentials."
                self.logger.error(message)
                raise QueueApi.AuthenticationError(message)

            case _:
                message = f"QPU returned unhandled status {result.status_code}."
                self.logger.error(message)
                raise QueueApi.QueueApiError(message)

        return QueueApi._result_as_json(result)

    def get_task_status_in_queue(self, task_id: Union[str, uuid.UUID]) -> dict:
        """
        Request task status in a queue for a given task.
        @param task_id: Task ID.
        @return: Parsed JSON of the task status.
        """
        url = self._get_path("queue", "task", str(task_id))
        self.logger.info(f'GETting task status queue from  "{url}".')
        result = requests.get(url, headers=self._generate_headers(), auth=self.auth)
        self.logger.debug(f"API return status {result.status_code}.")

        match result.status_code:
            case 200:
                message = "Successfully checked queue."
                self.logger.debug(message)

            case 400:
                message = (
                    "The request is invalid. This may indicate an error when"
                    " parsing a parameter."
                )
                self.logger.error(message)
                raise QueueApi.InvalidRequestError(message)

            case 404:
                message = f"QPU {self.qpu_id} or task {task_id} not found."
                self.logger.error(message)
                raise QueueApi.NotFound(message)

            case _:
                message = f"QPU returned unhandled status {result.status_code}."
                self.logger.error(message)
                raise QueueApi.QueueApiError(message)
        result_json = QueueApi._result_as_json(result)

        return result_json["status"]

    def cancel_task_in_queue(self, task_id: Union[str, uuid.UUID]):
        url = self._get_path("queue", "task", str(task_id), "cancel")
        self.logger.info(f'PUTting task status queue from  "{url}".')
        result = requests.put(url, headers=self._generate_headers(), auth=self.auth)
        self.logger.debug(f"API return status {result.status_code}.")

        match result.status_code:
            case 200:
                message = "Task successfully cancelled"
                self.logger.debug(message)

            case 403:
                message = "QPU return authentication error, check AWS credentials."
                self.logger.error(message)
                raise QueueApi.AuthenticationError(message)

            case 404:
                message = f"QPU {self.qpu_id} or task {task_id} not found."
                self.logger.error(message)
                raise QueueApi.NotFound(message)

            case _:
                message = f"QPU returned unhandled status {result.status_code}."
                self.logger.error(message)
                raise QueueApi.QueueApiError(message)

    def get_task_summary(self, task_id: Union[str, uuid.UUID]) -> dict:
        """
        Request the task summary for a given task.
        The summary contains the status of the current task.
        @param task_id: Task ID.
        @return: Parsed JSON of the task summary.
        @see: `TaskSummary` in https://github.com/QuEra-QCS/QCS-API/blob/master/qcs-api/openapi.yaml
        """
        url = "/".join((self.base_url, self.qpu_id, "task", str(task_id)))
        self.logger.info(f'GETting task summary from  "{url}".')
        result = requests.get(url, headers=self._generate_headers(), auth=self.auth)
        self.logger.debug(f"API return status {result.status_code}.")

        match result.status_code:
            case 200:
                message = "Successfully checked task summary."
                self.logger.warning(message)

            case 404:
                message = f"QPU {self.qpu_id} or task {task_id} not found."
                self.logger.error(message)
                raise QueueApi.NotFound(message)

            case 403:
                message = "QPU return authentication error, check AWS credentials."
                self.logger.error(message)
                raise QueueApi.AuthenticationError(message)

            case _:
                message = f"QPU returned unhandled status {result.status_code}."
                self.logger.error(message)
                raise QueueApi.QueueApiError(message)

        return QueueApi._result_as_json(result)

    def is_task_stopped(self, task_id: Union[str, uuid.UUID]) -> bool:
        """
        Check whether a task is stopped (because it is completed, failed, or cancelled).
        @param task_id:
        @return: `True` if task is stopped.
        """
        summary = self.get_task_status_in_queue(task_id)
        return summary["status"].lower() in ("completed", "failed", "cancelled")
