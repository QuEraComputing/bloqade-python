from bloqade.submission.ir.task_specification import QuEraTaskSpecification
import bloqade.submission.quera_api_client.api
from bloqade.submission.base import get_capabilities
from unittest.mock import patch
from requests import Response
import json
from typing import Dict

from bloqade import start
from bloqade.task.batch import RemoteBatch
import pytest
import os


# Integraiton tests
@pytest.mark.vcr
def test_quera_submit():
    credentials = {
        "access_key": "XXXXXXXXXXXXXXXXXXXX",
        "secret_key": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        "session_token": 900 * "X",
    }
    config_file = os.path.join("tests", "data", "config", "submit_quera_api.json")

    batch = (
        start.add_position((0, 0))
        .rydberg.rabi.amplitude.uniform.piecewise_linear(
            [0.1, "run_time", 0.1], [0, 15, 15, 0]
        )
        .assign(run_time=2.0)
        .parallelize(20)
        .quera.aquila(config_file=config_file, **credentials)
        .submit(shots=10)
    )

    bloqade.save_batch("quera_submit.json", batch)


@pytest.mark.vcr
def test_quera_retrieve():
    credentials = {
        "access_key": "XXXXXXXXXXXXXXXXXXXX",
        "secret_key": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        "session_token": 900 * "X",
    }

    job_future = bloqade.load_batch("quera_submit.json", **credentials)
    assert type(job_future) == RemoteBatch
    job_future.pull()


def create_response(
    status_code: int, content: Dict, content_type="application/json"
) -> Response:
    response = Response()
    response.status_code = status_code
    response.headers["Content-Type"] = content_type
    response._content = bytes(json.dumps(content), "utf-8")
    return response


def mock_task_ir():
    return {
        "nshots": 10,
        "lattice": {"sites": [(0, 0)], "filling": [1]},
        "effective_hamiltonian": {
            "rydberg": {
                "rabi_frequency_amplitude": {
                    "global": {
                        "times": [0, 1e-6, 2e-6, 3e-6, 4e-6],
                        "values": [0, 15e6, 15e6, 0],
                    },
                },
                "rabi_frequency_phase": {
                    "global": {"times": [0, 4e-6], "values": [0, 0]},
                },
                "detuning": {
                    "global": {
                        "times": [0, 1e-6, 2e-6, 3e-6, 4e-6],
                        "values": [0, 15e6, 15e6, 0],
                    },
                },
            }
        },
    }


def mock_results():
    return {
        "task_status": "Completed",
        "shot_outputs": [
            {"shot_status": "Completed", "pre_sequence": [1], "post_sequence": [1]},
            {"shot_status": "Completed", "pre_sequence": [1], "post_sequence": [1]},
            {"shot_status": "Completed", "pre_sequence": [1], "post_sequence": [1]},
            {"shot_status": "Completed", "pre_sequence": [1], "post_sequence": [1]},
            {"shot_status": "Completed", "pre_sequence": [1], "post_sequence": [1]},
            {"shot_status": "Completed", "pre_sequence": [1], "post_sequence": [1]},
            {"shot_status": "Completed", "pre_sequence": [1], "post_sequence": [1]},
            {"shot_status": "Completed", "pre_sequence": [1], "post_sequence": [1]},
            {"shot_status": "Completed", "pre_sequence": [1], "post_sequence": [1]},
            {"shot_status": "Completed", "pre_sequence": [1], "post_sequence": [1]},
        ],
    }


@patch("bloqade.submission.quera_api_client.api.Sigv4Request")
def test_happy_path_queue_api(*args):
    def mock_get(*args, **kwargs):
        print("get", args, kwargs)
        match (args, kwargs):
            case (
                ("https://https://api.que-ee.com/v0/qpu-1/capabilities",),
                {"headers": {"Content-Type": "application/json"}},
            ):
                return create_response(200, get_capabilities().dict())
            case (
                ("https://https://api.que-ee.com/v0/qpu-1/queue/task/task_id",),
                {"headers": {"Content-Type": "application/json"}},
            ):
                return create_response(200, {"status": "Completed"})
            case (
                ("https://https://api.que-ee.com/v0/qpu-1/task/task_id/results",),
                {"headers": {"Content-Type": "application/json"}},
            ):
                return create_response(200, mock_results())
            case _:
                raise NotImplementedError

    def mock_put(*args, **kwargs):
        print("put", args, kwargs)
        match (args, kwargs):
            case (
                ("https://https://api.que-ee.com/v0/qpu-1/queue/task/task_id/cancel",),
                {"headers": {"Content-Type": "application/json"}},
            ):
                return create_response(200, {})
            case _:
                raise NotImplementedError

    def mock_post(*args, **kwargs):
        print("post", args, kwargs)
        match (args, kwargs):
            case (
                ("https://https://api.que-ee.com/v0/qpu-1/queue/task",),
                {
                    "headers": {"Content-Type": "application/json"},
                    "data": str() as task_ir_string,
                },
            ):
                if QuEraTaskSpecification(
                    **json.loads(task_ir_string)
                ) != QuEraTaskSpecification(**mock_task_ir()):
                    raise ValueError("Task IRs do not match")

                return create_response(201, {"task_id": "task_id"})
            case _:
                raise NotImplementedError

    api_config = dict(
        api_hostname="https://api.que-ee.com", qpu_id="qpu-1", api_stage="v0"
    )

    sig_v4_config = dict(
        region="us-east-1",
        access_key=None,
        secret_key=None,
        session_token=None,
        session_expires=3600,
        role_arn=None,
        role_session_name="awsrequest",
        profile=None,
    )

    request_api = bloqade.submission.quera_api_client.api.Sigv4Request(**sig_v4_config)
    request_api.get.side_effect = mock_get
    request_api.post.side_effect = mock_post
    request_api.put.side_effect = mock_put
    queue = bloqade.submission.quera_api_client.api.QueueApi(**api_config)

    assert queue.get_capabilities() == get_capabilities().dict()
    assert queue.post_task(mock_task_ir()) == "task_id"
    assert queue.get_task_status_in_queue("task_id") == "Completed"
    assert queue.get_task_results("task_id") == mock_results()
    assert queue.is_task_stopped("task_id")
    assert queue.cancel_task_in_queue("task_id") is None


@patch("bloqade.submission.quera_api_client.api.Sigv4Request")
def test_task_results_polling(*args):
    api_config = dict(
        api_hostname="https://api.que-ee.com", qpu_id="qpu-1", api_stage="v0"
    )

    sig_v4_config = dict(
        region="us-east-1",
        access_key=None,
        secret_key=None,
        session_token=None,
        session_expires=3600,
        role_arn=None,
        role_session_name="awsrequest",
        profile=None,
    )

    request_api = bloqade.submission.quera_api_client.api.Sigv4Request(**sig_v4_config)
    queue = bloqade.submission.quera_api_client.api.QueueApi(**api_config)

    request_api.get.side_effect = [
        create_response(200, {"status": "Enqueued"}),
        create_response(200, {"status": "Enqueued"}),
        create_response(200, {"status": "Enqueued"}),
        create_response(200, {"status": "Accepted"}),
        create_response(200, {"status": "Created"}),
        create_response(200, {"status": "Running"}),
        create_response(200, {"status": "Completed"}),
        # calls get_task_status_in_queue before fetching results
        create_response(200, {"status": "Completed"}),
        create_response(200, mock_results()),
    ]

    assert queue.poll_task_results("task_id", polling_interval=0.5) == mock_results()


@patch("bloqade.submission.quera_api_client.api.Sigv4Request")
def test_post_task_error_paths(*args):
    api_config = dict(
        api_hostname="https://api.que-ee.com", qpu_id="qpu-1", api_stage="v0"
    )

    sig_v4_config = dict(
        region="us-east-1",
        access_key=None,
        secret_key=None,
        session_token=None,
        session_expires=3600,
        role_arn=None,
        role_session_name="awsrequest",
        profile=None,
    )

    QueueApi = bloqade.submission.quera_api_client.api.QueueApi
    request_api = bloqade.submission.quera_api_client.api.Sigv4Request(**sig_v4_config)
    queue = bloqade.submission.quera_api_client.api.QueueApi(**api_config)

    request_api.post.side_effect = [
        create_response(404, {}),
        create_response(400, {}),
        create_response(403, {}),
        create_response(500, {}),
        create_response(201, {"task_id_other": "task_id"}),
    ]

    with pytest.raises(QueueApi.NotFound):
        queue.post_task(mock_task_ir())

    with pytest.raises(QueueApi.InvalidRequestError):
        queue.post_task(mock_task_ir())

    with pytest.raises(QueueApi.AuthenticationError):
        queue.post_task(mock_task_ir())

    with pytest.raises(QueueApi.QueueApiError):
        queue.post_task(mock_task_ir())

    with pytest.raises(QueueApi.InvalidResponseError):
        queue.post_task(mock_task_ir())


@patch("bloqade.submission.quera_api_client.api.Sigv4Request")
def test_task_validation_error_paths(*args):
    api_config = dict(
        api_hostname="https://api.que-ee.com", qpu_id="qpu-1", api_stage="v0"
    )

    sig_v4_config = dict(
        region="us-east-1",
        access_key=None,
        secret_key=None,
        session_token=None,
        session_expires=3600,
        role_arn=None,
        role_session_name="awsrequest",
        profile=None,
    )

    QueueApi = bloqade.submission.quera_api_client.api.QueueApi
    request_api = bloqade.submission.quera_api_client.api.Sigv4Request(**sig_v4_config)
    queue = bloqade.submission.quera_api_client.api.QueueApi(**api_config)

    request_api.post.side_effect = [
        create_response(404, {}),
        create_response(400, {}),
        create_response(403, {}),
        create_response(500, {}),
    ]

    with pytest.raises(QueueApi.NotFound):
        queue.validate_task(mock_task_ir())

    with pytest.raises(QueueApi.ValidationError):
        queue.validate_task(mock_task_ir())

    with pytest.raises(QueueApi.AuthenticationError):
        queue.validate_task(mock_task_ir())

    with pytest.raises(QueueApi.QueueApiError):
        queue.validate_task(mock_task_ir())


@patch("bloqade.submission.quera_api_client.api.Sigv4Request")
def test_get_capabilities_error_paths(*args):
    api_config = dict(
        api_hostname="https://api.que-ee.com", qpu_id="qpu-1", api_stage="v0"
    )

    sig_v4_config = dict(
        region="us-east-1",
        access_key=None,
        secret_key=None,
        session_token=None,
        session_expires=3600,
        role_arn=None,
        role_session_name="awsrequest",
        profile=None,
    )

    QueueApi = bloqade.submission.quera_api_client.api.QueueApi
    request_api = bloqade.submission.quera_api_client.api.Sigv4Request(**sig_v4_config)
    queue = bloqade.submission.quera_api_client.api.QueueApi(**api_config)

    request_api.get.side_effect = [
        create_response(404, {}),
        create_response(403, {}),
        create_response(500, {}),
    ]

    with pytest.raises(QueueApi.NotFound):
        queue.get_capabilities()

    with pytest.raises(QueueApi.AuthenticationError):
        queue.get_capabilities()

    with pytest.raises(QueueApi.QueueApiError):
        queue.get_capabilities()


def test_api_requests_errors():
    api_config = dict(
        api_hostname="https://api.que-ee.com", qpu_id="qpu-1", api_stage="v0"
    )

    api_requests = bloqade.submission.quera_api_client.api.ApiRequest(**api_config)

    with pytest.raises(NotImplementedError):
        api_requests._post("https://api.que-ee.com/v0/qpu-1", {}, {})

    with pytest.raises(NotImplementedError):
        api_requests._put("https://api.que-ee.com/v0/qpu-1", {})

    with pytest.raises(NotImplementedError):
        api_requests._get("https://api.que-ee.com/v0/qpu-1", {})


@patch("bloqade.submission.quera_api_client.api.Sigv4Request")
def test_get_task_status_in_queue_error_paths(*args):
    api_config = dict(
        api_hostname="https://api.que-ee.com", qpu_id="qpu-1", api_stage="v0"
    )

    sig_v4_config = dict(
        region="us-east-1",
        access_key=None,
        secret_key=None,
        session_token=None,
        session_expires=3600,
        role_arn=None,
        role_session_name="awsrequest",
        profile=None,
    )

    QueueApi = bloqade.submission.quera_api_client.api.QueueApi
    request_api = bloqade.submission.quera_api_client.api.Sigv4Request(**sig_v4_config)
    queue = bloqade.submission.quera_api_client.api.QueueApi(**api_config)

    request_api.get.side_effect = [
        create_response(400, {}),
        create_response(404, {}),
        create_response(500, {}),
    ]

    with pytest.raises(QueueApi.InvalidRequestError):
        queue.get_task_status_in_queue("task_id")

    with pytest.raises(QueueApi.NotFound):
        queue.get_task_status_in_queue("task_id")

    with pytest.raises(QueueApi.QueueApiError):
        queue.get_task_status_in_queue("task_id")


@patch("bloqade.submission.quera_api_client.api.Sigv4Request")
def test_cancel_task_in_queue_error_paths(*args):
    api_config = dict(
        api_hostname="https://api.que-ee.com", qpu_id="qpu-1", api_stage="v0"
    )

    sig_v4_config = dict(
        region="us-east-1",
        access_key=None,
        secret_key=None,
        session_token=None,
        session_expires=3600,
        role_arn=None,
        role_session_name="awsrequest",
        profile=None,
    )

    QueueApi = bloqade.submission.quera_api_client.api.QueueApi
    request_api = bloqade.submission.quera_api_client.api.Sigv4Request(**sig_v4_config)
    queue = bloqade.submission.quera_api_client.api.QueueApi(**api_config)

    request_api.put.side_effect = [
        create_response(403, {}),
        create_response(404, {}),
        create_response(500, {}),
    ]

    with pytest.raises(QueueApi.AuthenticationError):
        queue.cancel_task_in_queue("task_id")

    with pytest.raises(QueueApi.NotFound):
        queue.cancel_task_in_queue("task_id")

    with pytest.raises(QueueApi.QueueApiError):
        queue.cancel_task_in_queue("task_id")


@patch("bloqade.submission.quera_api_client.api.Sigv4Request")
def test_get_task_results_paths(*args):
    from bloqade.submission.quera_api_client.api import ApiRequest

    api_config = dict(
        api_hostname="https://api.que-ee.com", qpu_id="qpu-1", api_stage="v0"
    )

    sig_v4_config = dict(
        region="us-east-1",
        access_key=None,
        secret_key=None,
        session_token=None,
        session_expires=3600,
        role_arn=None,
        role_session_name="awsrequest",
        profile=None,
    )

    QueueApi = bloqade.submission.quera_api_client.api.QueueApi
    request_api = bloqade.submission.quera_api_client.api.Sigv4Request(**sig_v4_config)
    queue = bloqade.submission.quera_api_client.api.QueueApi(**api_config)

    request_api.get.side_effect = [
        create_response(200, {"status": "Created"}),
        create_response(200, {"status": "Enqueued"}),
        create_response(200, {"status": "Accepted"}),
        # ----------------------------------------- #
        create_response(200, {"status": "Executing"}),
        # ----------------------------------------- #
        create_response(200, {"status": "Failed"}),
        create_response(200, {"status": "Cancelled"}),
        # ----------------------------------------- #
        create_response(200, {"status": "Unaccepted"}),
        # ----------------------------------------- #
        create_response(200, {"status": "OtherRandomMessage"}),
        # ----------------------------------------- #
        create_response(200, {"status": "Completed"}),
        create_response(400, {}),
        # ----------------------------------------- #
        create_response(200, {"status": "Completed"}),
        create_response(404, {}),
        # ----------------------------------------- #
        create_response(200, {"status": "Completed"}),
        create_response(403, {}),
        # ----------------------------------------- #
        create_response(200, {"status": "Completed"}),
        create_response(500, {}),
        # ----------------------------------------- #
        create_response(200, {"status": "Completed"}),
        create_response(200, {"status": "Completed"}, content_type="text/html"),
    ]

    assert queue.get_task_results("task_id") == {
        "task_status": "Created",
        "shot_outputs": [],
    }
    assert queue.get_task_results("task_id") == {
        "task_status": "Created",
        "shot_outputs": [],
    }
    assert queue.get_task_results("task_id") == {
        "task_status": "Created",
        "shot_outputs": [],
    }
    assert queue.get_task_results("task_id") == {
        "task_status": "Running",
        "shot_outputs": [],
    }
    assert queue.get_task_results("task_id") == {
        "task_status": "Failed",
        "shot_outputs": [],
    }
    assert queue.get_task_results("task_id") == {
        "task_status": "Cancelled",
        "shot_outputs": [],
    }

    with pytest.raises(QueueApi.ValidationError):
        queue.get_task_results("task_id")

    with pytest.raises(QueueApi.QueueApiError):
        queue.get_task_results("task_id")

    with pytest.raises(QueueApi.InvalidRequestError):
        queue.get_task_results("task_id")

    with pytest.raises(QueueApi.NotFound):
        queue.get_task_results("task_id")

    with pytest.raises(QueueApi.AuthenticationError):
        queue.get_task_results("task_id")

    with pytest.raises(QueueApi.QueueApiError):
        queue.get_task_results("task_id")

    with pytest.raises(ApiRequest.InvalidResponseError):
        queue.get_task_results("task_id")


@patch("bloqade.submission.quera_api_client.api.Sigv4Request")
def test_get_task_summary_paths(*args):
    api_config = dict(
        api_hostname="https://api.que-ee.com", qpu_id="qpu-1", api_stage="v0"
    )

    sig_v4_config = dict(
        region="us-east-1",
        access_key=None,
        secret_key=None,
        session_token=None,
        session_expires=3600,
        role_arn=None,
        role_session_name="awsrequest",
        profile=None,
    )

    QueueApi = bloqade.submission.quera_api_client.api.QueueApi
    request_api = bloqade.submission.quera_api_client.api.Sigv4Request(**sig_v4_config)
    queue = bloqade.submission.quera_api_client.api.QueueApi(**api_config)

    request_api.get.side_effect = [
        create_response(200, {"status": "Running"}),
        # ----------------------------------------- #
        create_response(200, {"status": "Completed"}),
        create_response(200, {"status": "Completed"}),
        # ----------------------------------------- #
        create_response(200, {"status": "Completed"}),
        create_response(404, {}),
        # ----------------------------------------- #
        create_response(200, {"status": "Completed"}),
        create_response(403, {}),
        # ----------------------------------------- #
        create_response(200, {"status": "Completed"}),
        create_response(500, {}),
        # ----------------------------------------- #
    ]

    with pytest.raises(QueueApi.QueueApiError):
        queue.get_task_summary("task_id")

    assert queue.get_task_summary("task_id") == {"status": "Completed"}

    with pytest.raises(QueueApi.NotFound):
        queue.get_task_summary("task_id")

    with pytest.raises(QueueApi.AuthenticationError):
        queue.get_task_summary("task_id")

    with pytest.raises(QueueApi.QueueApiError):
        queue.get_task_summary("task_id")
