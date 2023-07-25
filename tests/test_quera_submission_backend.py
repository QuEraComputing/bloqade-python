import pytest

import bloqade.submission.quera
import bloqade.submission.ir.task_specification as task_spec
from bloqade.submission.ir.task_results import QuEraTaskResults, QuEraTaskStatusCode
from bloqade.submission.base import ValidationError
from bloqade.submission.capabilities import get_capabilities
from bloqade.submission.ir.capabilities import QuEraCapabilities

from unittest.mock import patch


def get_task_ir():
    return task_spec.QuEraTaskSpecification(
        nshots=10,
        lattice=task_spec.Lattice(sites=[(0, 0)], filling=[1]),
        effective_hamiltonian=task_spec.EffectiveHamiltonian(
            rydberg=task_spec.RydbergHamiltonian(
                rabi_frequency_amplitude=task_spec.RabiFrequencyAmplitude(
                    global_=task_spec.GlobalField(
                        times=[0, 1e-6, 2e-6, 3e-6, 4e-6],
                        values=[0, 15e6, 15e6, 0],
                    )
                ),
                rabi_frequency_phase=task_spec.RabiFrequencyPhase(
                    global_=task_spec.GlobalField(
                        times=[0, 4e-6],
                        values=[0, 0],
                    )
                ),
                detuning=task_spec.Detuning(
                    global_=task_spec.GlobalField(
                        times=[0, 1e-6, 2e-6, 3e-6, 4e-6],
                        values=[0, 15e6, 15e6, 0],
                    )
                ),
            )
        ),
    )


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


@patch("bloqade.submission.quera.QueueApi")
def test_quera_backend_submit(*args):
    api_config = dict(
        api_hostname="https://api.que-ee.com", qpu_id="qpu-1", api_stage="v0"
    )

    queue = bloqade.submission.quera.QueueApi(**api_config)

    queue.post_task.return_value = "task_id"

    backend = bloqade.submission.quera.QuEraBackend(**api_config)

    assert backend.submit_task(get_task_ir()) == "task_id"
    queue.post_task.assert_called_once()


@patch("bloqade.submission.quera.QueueApi")
def test_quera_backend_validate(QueueApi):
    api_config = dict(
        api_hostname="https://api.que-ee.com", qpu_id="qpu-1", api_stage="v0"
    )

    bloqade.submission.quera.QueueApi.ValidationError = (
        Exception  # spoof ValidationError
    )
    queue = bloqade.submission.quera.QueueApi(**api_config)

    queue.validate_task.side_effect = bloqade.submission.quera.QueueApi.ValidationError(
        "error"
    )

    backend = bloqade.submission.quera.QuEraBackend(**api_config)

    with pytest.raises(ValidationError):
        backend.validate_task(get_task_ir())

    queue.validate_task.assert_called_once()

    queue.reset_mock()

    queue.validate_task.side_effect = None

    assert backend.validate_task(get_task_ir()) is None

    queue.validate_task.assert_called_once()


@patch("bloqade.submission.quera.QueueApi")
def test_quera_backend_cancel(QueueApi):
    api_config = dict(
        api_hostname="https://api.que-ee.com", qpu_id="qpu-1", api_stage="v0"
    )

    queue = bloqade.submission.quera.QueueApi(**api_config)

    backend = bloqade.submission.quera.QuEraBackend(**api_config)

    backend.cancel_task("task_id")

    queue.cancel_task_in_queue.assert_called_once_with("task_id")


@patch("bloqade.submission.quera.QueueApi")
def test_quera_backend_status(QueueApi):
    api_config = dict(
        api_hostname="https://api.que-ee.com", qpu_id="qpu-1", api_stage="v0"
    )

    queue = bloqade.submission.quera.QueueApi(**api_config)

    queue.get_task_status_in_queue.return_value = "Completed"

    backend = bloqade.submission.quera.QuEraBackend(**api_config)

    assert backend.task_status("task_id") == QuEraTaskStatusCode.Completed

    queue.get_task_status_in_queue.assert_called_once_with("task_id")


@patch("bloqade.submission.quera.QueueApi")
def teest_quera_backend_task_results(QueueApi):
    api_config = dict(
        api_hostname="https://api.que-ee.com", qpu_id="qpu-1", api_stage="v0"
    )

    queue = bloqade.submission.quera.QueueApi(**api_config)

    queue.poll_task_results.return_value = mock_results()

    backend = bloqade.submission.quera.QuEraBackend(**api_config)

    assert backend.task_results("task_id") == QuEraTaskResults(**mock_results())

    queue.poll_task_results.assert_called_once_with("task_id")


@patch("bloqade.submission.quera.QueueApi")
def test_quera_backend_get_capabilities(QueueApi):
    api_config = dict(
        api_hostname="https://api.que-ee.com", qpu_id="qpu-1", api_stage="v0"
    )
    capabilities_dict = get_capabilities().dict()

    queue = bloqade.submission.quera.QueueApi(**api_config)
    queue.get_capabilities.return_value = capabilities_dict

    backend = bloqade.submission.quera.QuEraBackend(**api_config)

    assert backend.get_capabilities() == QuEraCapabilities(**capabilities_dict)
    queue.get_capabilities.assert_called_once()

    queue.reset_mock()

    queue.get_capabilities.return_value = Exception("error")
    backend = bloqade.submission.quera.QuEraBackend(**api_config)

    assert backend.get_capabilities() == QuEraCapabilities(**get_capabilities().dict())
    queue.get_capabilities.assert_called_once()
