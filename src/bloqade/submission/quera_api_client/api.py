import json
import logging
from types import NoneType
import uuid
from typing import Optional, Union, Dict, Tuple
import requests
from requests_sigv4 import Sigv4Request


class ApiRequest:
    """Class that defines base methods for API requests."""

    class ApiRequestError(Exception):
        pass

    class InvalidResponseError(ApiRequestError):
        pass

    def __init__(
        self,
        api_hostname: str,
        qpu_id: str,
        api_stage="v0",
        proxy: Optional[str] = None,
    ):
        """
        Create an instance of `ApiRequest`.
        @param api_hostname: hostname of the API instance.
        @param qpu_id: The QPU ID, for example `qpu1-mock`.
        @param api_stage: Specify which version of the API to call from this object.
        @param proxy: Optional, the hostname for running the API via some proxy
        endpoint.
        """

        if proxy is None:
            self.hostname = None
            self.aws_host = api_hostname
            uri_with_version = api_hostname + f"/{api_stage}"
        else:
            self.hostname = api_hostname
            self.aws_host = proxy
            uri_with_version = proxy + f"/{api_stage}"

        self.base_url = "https://" + uri_with_version
        self.qpu_id = qpu_id
        self.logger = logging.getLogger(self.__class__.__name__)

    @staticmethod
    def _result_as_json(result: requests.Response) -> dict:
        content_type = result.headers["Content-Type"]
        if content_type != "application/json":
            raise ApiRequest.InvalidResponseError(
                f"Expected Content-Type application/json, but {content_type} found."
            )

        if len(result.content) == 0:
            return {}

        return json.loads(result.content)

    def _generate_headers(self, base: Optional[dict] = None) -> dict:
        match (base, self.hostname):
            case (None, None):
                return {"Content-Type": "application/json"}
            case (None, _):
                return {"Content-Type": "application/json", "Host": self.hostname}
            case (_, None):
                return base
            case _:
                header = dict(base)
                header["Host"] = self.hostname
                return header

    def _get_path(self, *path_list: str):
        return "/".join((self.base_url, self.qpu_id) + path_list)

    def _prepare_request(self, *path_list: str) -> Tuple[str, Dict[str, str]]:
        headers = self._generate_headers()
        url = self._get_path(*path_list)
        return url, headers

    def _post(
        self, url: str, headers: Dict[str, str], content: str
    ) -> requests.Response:
        raise NotImplementedError

    def _get(self, url: str, headers: Dict[str, str]) -> requests.Response:
        raise NotImplementedError

    def _put(self, url: str, headers: Dict[str, str]) -> requests.Response:
        raise NotImplementedError

    # public API
    def post(self, *path_list: str, content: Dict[str, str] = {}) -> requests.Response:
        url, headers = self._prepare_request(*path_list)

        if type(content) == dict:
            content = json.dumps(content)

        self.logger.info(f'POSTing to "{url}".')
        response = self._post(url, headers, content)
        self.logger.debug(f"API return status {response.status_code}.")
        return response

    def get(self, *path_list: str) -> requests.Response:
        url, headers = self._prepare_request(*path_list)
        self.logger.info(f'GETting "{url}".')
        response = self._get(url, headers)
        self.logger.debug(f"API return status {response.status_code}.")
        return response

    def put(self, *path_list: str) -> requests.Response:
        url, headers = self._prepare_request(*path_list)
        self.logger.info(f'PUTting "{url}".')
        response = self._put(url, headers)
        self.logger.debug(f"API return status {response.status_code}.")
        return response


class AwsApiRequest(ApiRequest):
    def __init__(
        self,
        api_hostname: str,
        qpu_id: str,
        api_stage="v0",
        proxy: Optional[str] = None,
        # Sigv4Request arguments
        region: str = "us-east-1",
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        session_token: Optional[str] = None,
        session_expires: int = 3600,
        role_arn: Optional[str] = None,
        role_session_name: str = "awsrequest",
        profile: Optional[str] = None,
    ):
        """
        Create an instance of `AwsApiRequest`.
        @param api_hostname: hostname of the API instance.
        @param qpu_id: The QPU ID, for example `qpu1-mock`.
        @param api_stage: Specify which version of the API to call from this object.
        @param proxy: Optional, the hostname for running the API via some proxy
        endpoint.
        @param region: AWS region, default value: "us-east-1"
        @param access_key: Optional, AWS account access key
        @param secret_key: Optional, AWS account secret key
        @param session_token: Optional, AWS session token
        @param session_expires: int, time before current tokens expire, default value
        3600
        @param role_arn: Optional, AWS role ARN
        @param role_session_name: AWS role session name, defualy value: 'awsrequest',
        @param profile: Optional, AWS profile to use credentials for.
        """
        super().__init__(api_hostname, qpu_id, api_stage=api_stage, proxy=proxy)

        self.request = Sigv4Request(
            region=region,
            access_key=access_key,
            secret_key=secret_key,
            session_token=session_token,
            session_expires=session_expires,
            role_arn=role_arn,
            role_session_name=role_session_name,
            profile=profile,
        )

    def _post(
        self, url: str, headers: Dict[str, str], content: Dict[str, str]
    ) -> requests.Response:
        return self.request.post(url, headers=headers, data=content)

    def _get(self, url: str, headers: Dict[str, str]) -> requests.Response:
        return self.request.get(url, headers=headers)

    def _put(self, url: str, headers: Dict[str, str]) -> requests.Response:
        return self.request.put(url, headers=headers)


class QueueApi:
    """Simple interface to the QCS task API.

    Example (replace URIs, QPU ID with correct values):
    >>> task_json = {
    ...     "nshots": 10,
    ...     "lattice": {
    ...         "sites":[[0,0]],
    ...         "filling":[1],
    ...     },
    ...     "effective_hamiltonian": {
    ...         "rydberg": {
    ...             "rabi_frequency_amplitude":{
    ...                 "global": {
    ...                     "times":[0.0, 0.1e-6, 3.9e-6, 4.0e-6],
    ...                     "values":[0.0, 15.0e6, 15.0e6, 0.0],
    ...                 }
    ...             },
    ...             "rabi_frequency_phase": {
    ...                 "global": {
    ...                 "times":[0.0, 4.0e-6],
    ...                 "values":[0.0, 0.0],
    ...                 }
    ...             },
    ...             "detuning":{
    ...                 "global": {
    ...                     "times":[0.0, 4.0e-6],
    ...                     "values":[0.0, 0.0],
    ...                 }
    ...             }
    ...         }
    ...     }
    ... }
    To Use this class with API-Gateway:
    >>> api_hostname = "XXX.execute-api.us-east-1.amazonaws.com"
    >>> vpce_uri = "vpce-XXX-XXX.execute-api.us-east-1.vpce.amazonaws.com"
    >>> api = QueueApi(api_hostname, "qpu1-mock", proxy=vpce_uri)
    >>> print(api.get_capabilities())
    """

    bad_request = (
        "The request is invalid. This may indicate an error when parsing a parameter."
    )
    bad_submit_task_request = (
        "The request is invalid. This may indicate an error when parsing a parameter, "
        "or an error when parsing or validating the request body. The response body "
        "may contain a JSON array with a list of validation errors."
    )

    qpu_not_found = (
        "The QPU targeted by the request does not exist, or the user "
        "making the request is not authorized to access the targeted QPU."
    )
    qpu_or_task_not_found = (
        "The QPU or task targeted by the request does not exist, "
        "or the user making the request is not authorized to access the targeted QPU "
        "or task."
    )

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
        api_hostname: str,
        qpu_id: str,
        api_stage="v0",
        proxy: Optional[str] = None,
        **request_sigv4_kwargs,
    ):
        """
        Create an instance of `QueueApi`.
        @param api_hostname: hostname of the API instance.
        @param qpu_id: The QPU ID, for example `qpu1-mock`.
        @param api_stage: Specify which version of the API to call from this object.
        @param proxy: Optional, the hostname for running the API via some proxy
        endpoint.

        request_sigv4_kwargs:

        @param region: AWS region, default value: "us-east-1"
        @param access_key: Optional, AWS account access key
        @param secret_key: Optional, AWS account secret key
        @param session_token: Optional, AWS session token
        @param session_expires: int, time before current tokens expire, default value
        3600
        @param role_arn: Optional, AWS role ARN
        @param role_session_name: AWS role session name, defualy value: 'awsrequest',
        @param profile: Optional, AWS profile to use credentials for.
        """
        self.api_http_request = AwsApiRequest(
            api_hostname,
            qpu_id,
            api_stage=api_stage,
            proxy=proxy,
            **request_sigv4_kwargs,
        )

        self.logger = logging.getLogger(self.__class__.__name__)

    def post_task(self, task_json: Union[str, dict]) -> str:
        """
        Submit a task to the QPU via the task API.
        @param content: Task specification as a JSON string or dictionary.
        """
        result = self.api_http_request.post("queue", "task", content=task_json)

        match result.status_code:
            case 201:
                message = "Successfully posted task."
                self.logger.warning(message)

            case 404:
                message = f"QPU {self.api_http_request.qpu_id} not found."
                self.logger.error(message)
                raise QueueApi.NotFound(message)

            case 400:
                message = (
                    "The request is invalid. This may indicate an error when parsing "
                    "a parameter."
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

        result_json = ApiRequest._result_as_json(result)

        try:
            task_id = result_json["task_id"]
            self.logger.info(
                f"QPU {self.api_http_request.qpu_id} accepted "
                f"task with task id {task_id}."
            )
            return task_id
        except KeyError:
            raise QueueApi.InvalidResponseError('Response did not contain "task_id".')

    def get_capabilities(self) -> dict:
        """
        Request the QPU capabilities from the task API.
        @return: dictionary containing different fields for capabilities.
        """
        result = self.api_http_request.get("capabilities")

        match result.status_code:
            case 200:
                message = "Successfully fetched capabilities."
                self.logger.error(message)

            case 404:
                message = f"QPU {self.api_http_request.qpu_id} not found."
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

        return ApiRequest._result_as_json(result)

    def validate_task(self, task_json: Union[str, dict]) -> NoneType:
        result = self.api_http_request.post("task", "validate", content=task_json)

        match result.status_code:
            case 200:
                message = "Task passed validation."
                self.logger.info(message)

            case 400:
                message = f"Task did not pass validation: {result.text}"
                self.logger.error(message)
                raise QueueApi.ValidationError(message)

            case 404:
                message = f"QPU {self.api_http_request.qpu_id} not found."
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
                    f"Task: {task_id} has validation error, "
                    "unable to fetch error message."
                )
            case "Completed":
                pass
            case _:
                raise QueueApi.QueueApiError(
                    f"Undocumented queue status: {queue_status}"
                )

        result = self.api_http_request.get("task", str(task_id), "results")

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

        return ApiRequest._result_as_json(result)

    def get_task_status_in_queue(self, task_id: Union[str, uuid.UUID]) -> dict:
        """
        Request task status in a queue for a given task.
        @param task_id: Task ID.
        @return: Parsed JSON of the task status.
        """
        result = self.api_http_request.get("queue", "task", str(task_id))

        match result.status_code:
            case 200:
                message = "Successfully checked queue."
                self.logger.debug(message)

            case 400:
                message = (
                    "The request is invalid. This may indicate an error when parsing a "
                    "parameter."
                )
                self.logger.error(message)
                raise QueueApi.InvalidRequestError(message)

            case 404:
                message = (
                    f"QPU {self.api_http_request.qpu_id} or task {task_id} not found."
                )
                self.logger.error(message)
                raise QueueApi.NotFound(message)

            case _:
                message = f"QPU returned unhandled status {result.status_code}."
                self.logger.error(message)
                raise QueueApi.QueueApiError(message)
        result_json = ApiRequest._result_as_json(result)

        return result_json["status"]

    def cancel_task_in_queue(self, task_id: Union[str, uuid.UUID]):
        result = self.api_http_request.put("queue", "task", str(task_id), "cancel")

        match result.status_code:
            case 200:
                message = "Task successfully cancelled"
                self.logger.debug(message)

            case 403:
                message = "QPU return authentication error, check AWS credentials."
                self.logger.error(message)
                raise QueueApi.AuthenticationError(message)

            case 404:
                message = (
                    f"QPU {self.api_http_request.qpu_id} or task {task_id} not found."
                )
                self.logger.error(message)
                raise QueueApi.NotFound(message)

            case _:
                message = f"QPU returned unhandled status {result.status_code}."
                self.logger.error(message)
                raise QueueApi.QueueApiError(message)

    def get_task_summary(self, task_id: Union[str, uuid.UUID]) -> dict:
        """
        Request the task summary for a given task. The summary contains the status of
        the current task.
        @param task_id: Task ID.
        @return: Parsed JSON of the task summary.
        @see: `TaskSummary` in https://github.com/QuEra-QCS/QCS-API/blob/master/qcs-api/openapi.yaml
        """
        result = self.api_http_request.get("task", str(task_id))

        match result.status_code:
            case 200:
                message = "Successfully checked task summary."
                self.logger.warning(message)

            case 404:
                message = (
                    f"QPU {self.api_http_request.qpu_id} or task {task_id} not found."
                )
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

        return ApiRequest._result_as_json(result)

    def is_task_stopped(self, task_id: Union[str, uuid.UUID]) -> bool:
        """
        Check whether a task is stopped (because it is completed, failed, or cancelled).
        @param task_id:
        @return: `True` if task is stopped.
        """
        summary = self.get_task_status_in_queue(task_id)
        return summary["status"].lower() in ("completed", "failed", "cancelled")
