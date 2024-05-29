from bloqade import start
from requests import Response
from typing import Dict, List, Union
import simplejson as json

import bloqade.ir.routine.quera  # noqa: F401
from unittest.mock import patch
import pytest


def create_response(
    status_code: int, content: Union[Dict, List[Dict]], content_type="application/json"
) -> Response:
    response = Response()
    response.status_code = status_code
    response.headers["Content-Type"] = content_type
    response._content = bytes(json.dumps(content, use_decimal=True), "utf-8")
    return response


@patch("bloqade.ir.routine.quera.request")
def test_custom_submission(request_mock):
    body_template = '{{"token": "token", "body":{task_ir}}}'

    task_ids = ["1", "2", "3"]
    request_mock.side_effect = [
        create_response(200, {"task_id": task_id}) for task_id in task_ids
    ]

    # build bloqade program
    program = (
        start.add_position((0, 0))
        .rydberg.rabi.amplitude.uniform.piecewise_linear(
            [0.1, "time", 0.1], [0, 15, 15, 0]
        )
        .batch_assign(time=[0.0, 0.1, 0.5])
    )

    # submit and get responses and meta data associated with each task in the batch
    responses = program.quera.custom().submit(
        100, "https://my_service.test", body_template
    )

    for task_id, (metadata, response) in zip(task_ids, responses):
        response_json = response.json()
        assert response_json["task_id"] == task_id


@patch("bloqade.ir.routine.quera.request")
def test_custom_submission_error_missing_task_ir_key(request_mock):
    body_template = '{{"token": "token", "body":}}'

    task_ids = ["1", "2", "3"]
    request_mock.side_effect = [
        create_response(200, {"task_id": task_id}) for task_id in task_ids
    ]

    # build bloqade program
    program = (
        start.add_position((0, 0))
        .rydberg.rabi.amplitude.uniform.piecewise_linear(
            [0.1, "time", 0.1], [0, 15, 15, 0]
        )
        .batch_assign(time=[0.0, 0.1, 0.5])
    )
    with pytest.raises(ValueError):
        # submit and get responses and meta data associated with each task in the batch
        program.quera.custom().submit(100, "https://my_service.test", body_template)


@patch("bloqade.ir.routine.quera.request")
def test_custom_submission_error_malformed_template(request_mock):
    body_template = '{{"token": token", "body":}}'

    task_ids = ["1", "2", "3"]
    request_mock.side_effect = [
        create_response(200, {"task_id": task_id}) for task_id in task_ids
    ]

    # build bloqade program
    program = (
        start.add_position((0, 0))
        .rydberg.rabi.amplitude.uniform.piecewise_linear(
            [0.1, "time", 0.1], [0, 15, 15, 0]
        )
        .batch_assign(time=[0.0, 0.1, 0.5])
    )
    with pytest.raises(ValueError):
        # submit and get responses and meta data associated with each task in the batch
        program.quera.custom().submit(100, "https://my_service.test", body_template)
