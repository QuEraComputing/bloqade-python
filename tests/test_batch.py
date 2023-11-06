import pytest
from bloqade import start
import numpy as np
from unittest.mock import patch
from bloqade.submission.ir.task_results import QuEraTaskStatusCode, QuEraTaskResults
from bloqade.submission.ir.task_specification import QuEraTaskSpecification
from bloqade.task.base import Geometry
from bloqade.task.quera import QuEraTask
from bloqade.submission.base import ValidationError
from bloqade import dumps, loads

# import numpy as np


def mock_results_json(L):
    pre_sequence = np.array([0] + [1] * (L - 1))
    post_sequence = pre_sequence * np.random.choice(2, size=L)

    pre_sequence = pre_sequence.tolist()
    post_sequence = post_sequence.tolist()
    return {
        "task_status": "Completed",
        "shot_outputs": [
            {
                "shot_status": "Completed",
                "pre_sequence": pre_sequence,
                "post_sequence": post_sequence,
            },
            {
                "shot_status": "Completed",
                "pre_sequence": pre_sequence,
                "post_sequence": post_sequence,
            },
            {
                "shot_status": "Completed",
                "pre_sequence": pre_sequence,
                "post_sequence": post_sequence,
            },
            {
                "shot_status": "Completed",
                "pre_sequence": pre_sequence,
                "post_sequence": post_sequence,
            },
            {
                "shot_status": "Completed",
                "pre_sequence": pre_sequence,
                "post_sequence": post_sequence,
            },
            {
                "shot_status": "Completed",
                "pre_sequence": pre_sequence,
                "post_sequence": post_sequence,
            },
            {
                "shot_status": "Completed",
                "pre_sequence": pre_sequence,
                "post_sequence": post_sequence,
            },
            {
                "shot_status": "Completed",
                "pre_sequence": pre_sequence,
                "post_sequence": post_sequence,
            },
            {
                "shot_status": "Completed",
                "pre_sequence": pre_sequence,
                "post_sequence": post_sequence,
            },
            {
                "shot_status": "Completed",
                "pre_sequence": pre_sequence,
                "post_sequence": post_sequence,
            },
        ],
    }


def mock_task_ir(L):
    return {
        "nshots": 10,
        "lattice": {"sites": L * [(0, 0)], "filling": L * [1]},
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


def mock_task(L):
    return QuEraTaskSpecification(**mock_task_ir(L))


def mock_results(L):
    return QuEraTaskResults(**mock_results_json(L))


def test_base_classes():
    from bloqade.task.base import Task, LocalTask, RemoteTask

    task = Task()

    with pytest.raises(NotImplementedError):
        task.geometry

    task = LocalTask()

    with pytest.raises(NotImplementedError):
        task.result()

    with pytest.raises(NotImplementedError):
        task.run()

    task = RemoteTask()

    with pytest.raises(NotImplementedError):
        task.validate()

    with pytest.raises(NotImplementedError):
        task.result()

    with pytest.raises(NotImplementedError):
        task.fetch()

    with pytest.raises(NotImplementedError):
        task.status()

    with pytest.raises(NotImplementedError):
        task.pull()

    with pytest.raises(NotImplementedError):
        task.cancel()

    with pytest.raises(NotImplementedError):
        task.submit(True)

    with pytest.raises(NotImplementedError):
        task._result_exists()


@patch("bloqade.ir.routine.braket.BraketBackend")
@patch("bloqade.task.batch.np.random.permutation")
def test_remote_batch_task_metric(permutation, BraketBackend):
    backend = BraketBackend(
        device_arn="arn:aws:braket:us-east-1::device/qpu/quera/Aquila"
    )
    permutation.return_value = [0, 1, 2, 3, 4, 5]

    backend.submit_task.side_effect = list(map(str, range(6)))

    batch = (
        start.add_position([(0, i * 6.1) for i in range(14)])
        .rydberg.detuning.uniform.piecewise_linear(
            [0.1, 3.8, 0.1], [-20, -20, "d", "d"]
        )
        .amplitude.uniform.piecewise_linear([0.1, 3.8, 0.1], [0, 15, 15, 0])
        .phase.uniform.constant(np.pi / 2, 4)
        .batch_assign(d=[1, 2, 4, 8, 16, 32])
        .braket.aquila()
        ._compile(10)
    )

    for k, task in batch.tasks.items():
        task.backend = backend

    batch._submit(ignore_submission_error=True, shuffle_submit_order=True)

    assert str(batch) == (
        "  task ID    status  shots\n"
        "0       0  Enqueued     10\n"
        "1       1  Enqueued     10\n"
        "2       2  Enqueued     10\n"
        "3       3  Enqueued     10\n"
        "4       4  Enqueued     10\n"
        "5       5  Enqueued     10"
    )

    assert batch.total_nshots == 60


@patch("bloqade.ir.routine.braket.BraketBackend")
def test_remove_invalid_tasks(BraketBackend):
    backend = BraketBackend(
        device_arn="arn:aws:braket:us-east-1::device/qpu/quera/Aquila"
    )

    backend.submit_task.side_effect = list(map(str, range(6)))
    backend.task_status.return_value = QuEraTaskStatusCode.Unaccepted

    batch = (
        start.add_position([(0, i * 6.1) for i in range(14)])
        .rydberg.detuning.uniform.piecewise_linear(
            [0.1, 3.8, 0.1], [-20, -20, "d", "d"]
        )
        .amplitude.uniform.piecewise_linear([0.1, 3.8, 0.1], [0, 15, 15, 0])
        .phase.uniform.constant(np.pi / 2, 4)
        .batch_assign(d=[1, 2, 4, 8, 16, 32])
        .braket.aquila()
        ._compile(10)
    )

    for k, task in batch.tasks.items():
        task.backend = backend

    batch._submit(ignore_submission_error=True, shuffle_submit_order=False)
    batch.fetch()
    new_batch = batch.remove_invalid_tasks()
    assert len(new_batch.tasks) == 0


@patch("bloqade.ir.routine.braket.BraketBackend")
def test_test_filters(BraketBackend):
    backend = BraketBackend(
        device_arn="arn:aws:braket:us-east-1::device/qpu/quera/Aquila"
    )

    backend.submit_task.side_effect = list(map(str, range(6)))
    backend.task_status.side_effect = [
        QuEraTaskStatusCode.Failed,
        QuEraTaskStatusCode.Cancelled,
        QuEraTaskStatusCode.Completed,
        QuEraTaskStatusCode.Completed,
        QuEraTaskStatusCode.Completed,
        QuEraTaskStatusCode.Completed,
        QuEraTaskStatusCode.Completed,
    ]

    backend.task_results.return_value = mock_results(14)

    batch = (
        start.add_position([(0, i * 6.1) for i in range(14)])
        .rydberg.detuning.uniform.piecewise_linear(
            [0.1, 3.8, 0.1], [-20, -20, "d", "d"]
        )
        .amplitude.uniform.piecewise_linear([0.1, 3.8, 0.1], [0, 15, 15, 0])
        .phase.uniform.constant(np.pi / 2, 4)
        .batch_assign(d=[1, 2, 4, 8, 16, 32])
        .braket.aquila()
        ._compile(10)
    )

    for k, task in batch.tasks.items():
        task.backend = backend

    batch._submit(ignore_submission_error=True, shuffle_submit_order=False)
    batch.fetch()

    new_batch = batch.get_completed_tasks()
    assert len(new_batch.tasks) == 4

    new_batch = batch.get_failed_tasks()
    assert len(new_batch.tasks) == 1

    new_batch = batch.remove_failed_tasks()
    assert len(new_batch.tasks) == 5

    new_batch = batch.get_finished_tasks()
    assert len(new_batch.tasks) == 6


@patch("bloqade.ir.routine.braket.BraketBackend")
def test_cancel_tasks(BraketBackend):
    backend = BraketBackend(
        device_arn="arn:aws:braket:us-east-1::device/qpu/quera/Aquila"
    )

    backend.submit_task.side_effect = list(map(str, range(6)))
    backend.cancel_task.return_value = None

    batch = (
        start.add_position([(0, i * 6.1) for i in range(14)])
        .rydberg.detuning.uniform.piecewise_linear(
            [0.1, 3.8, 0.1], [-20, -20, "d", "d"]
        )
        .amplitude.uniform.piecewise_linear([0.1, 3.8, 0.1], [0, 15, 15, 0])
        .phase.uniform.constant(np.pi / 2, 4)
        .batch_assign(d=[1, 2, 4, 8, 16, 32])
        .braket.aquila()
        ._compile(10)
    )

    for k, task in batch.tasks.items():
        task.backend = backend

    batch._submit(ignore_submission_error=True, shuffle_submit_order=False)
    batch.cancel()

    assert backend.cancel_task.call_count == 6


@patch("bloqade.ir.routine.braket.BraketBackend")
def test_resubmit_tasks(BraketBackend):
    backend = BraketBackend(
        device_arn="arn:aws:braket:us-east-1::device/qpu/quera/Aquila"
    )

    backend.submit_task.side_effect = list(map(str, range(12)))

    batch = (
        start.add_position([(0, i * 6.1) for i in range(14)])
        .rydberg.detuning.uniform.piecewise_linear(
            [0.1, 3.8, 0.1], [-20, -20, "d", "d"]
        )
        .amplitude.uniform.piecewise_linear([0.1, 3.8, 0.1], [0, 15, 15, 0])
        .phase.uniform.constant(np.pi / 2, 4)
        .batch_assign(d=[1, 2, 4, 8, 16, 32])
        .braket.aquila()
        ._compile(10, name="test")
    )

    for k, task in batch.tasks.items():
        task.backend = backend

    batch._submit(ignore_submission_error=True, shuffle_submit_order=False)
    batch.resubmit(shuffle_submit_order=False)
    print(batch)
    assert str(batch) == (
        "  task ID    status  shots\n"
        "0       6  Enqueued     10\n"
        "1       7  Enqueued     10\n"
        "2       8  Enqueued     10\n"
        "3       9  Enqueued     10\n"
        "4      10  Enqueued     10\n"
        "5      11  Enqueued     10"
    )


@patch("bloqade.ir.routine.braket.BraketBackend")
def test_report(BraketBackend):
    backend = BraketBackend(
        device_arn="arn:aws:braket:us-east-1::device/qpu/quera/Aquila"
    )

    backend.submit_task.side_effect = list(map(str, range(6)))
    backend.task_status.side_effect = [
        QuEraTaskStatusCode.Failed,
        QuEraTaskStatusCode.Partial,
        QuEraTaskStatusCode.Completed,
        QuEraTaskStatusCode.Completed,
        QuEraTaskStatusCode.Completed,
        QuEraTaskStatusCode.Cancelled,
    ]

    backend.task_results.return_value = mock_results(14)

    batch = (
        start.add_position([(0, i * 6.1) for i in range(14)])
        .rydberg.detuning.uniform.piecewise_linear(
            [0.1, 3.8, 0.1], [-20, -20, "d", "d"]
        )
        .amplitude.uniform.piecewise_linear([0.1, 3.8, 0.1], [0, 15, 15, 0])
        .phase.uniform.constant(np.pi / 2, 4)
        .batch_assign(d=[1, 2, 4, 8, 16, 32])
        .braket.aquila()
        ._compile(10)
    )

    for k, task in batch.tasks.items():
        task.backend = backend

    batch._submit(ignore_submission_error=True, shuffle_submit_order=False)
    batch.fetch()
    report = batch.report()

    assert report.list_param("d") == [2.0, 4.0, 8.0, 16.0]
    assert report.markdown == (report.dataframe.to_markdown())

    assert all([len(ele) == 0 for ele in report.bitstrings(True)])
    assert all([len(ele) == 10 for ele in report.bitstrings(False)])
    assert all([len(ele) == 0 for ele in report.counts])


@patch("bloqade.task.quera.QuEraBackend")
def test_quera_task(QuEraBackend):
    backend = QuEraBackend()

    task = QuEraTask(
        task_id=None,
        backend=backend,
        task_ir=mock_task(14),
        metadata={},
    )

    assert task.nshots == 10
    assert task.geometry == Geometry([(0, 0)] * 14, [1] * 14)
    assert task.status() == QuEraTaskStatusCode.Unsubmitted
    assert not task._result_exists()

    with pytest.warns(Warning):
        task.cancel()

    with pytest.raises(ValueError):
        task.fetch()

    with pytest.raises(ValueError):
        task.pull()

    backend.submit_task.side_effect = ["1", "2"]

    task.submit()
    assert task.task_id == "1"

    with pytest.raises(ValueError):
        task.submit()

    task.submit(True)
    assert task.task_id == "2"

    backend.validate_task.return_value = None

    assert task.validate() == ""

    backend.validate_task.side_effect = ValidationError("test")
    assert task.validate() == "test"

    backend.task_status.return_value = QuEraTaskStatusCode.Completed
    mock_result = mock_results(14)
    backend.task_results.return_value = mock_result
    task.fetch()

    assert task.status() == QuEraTaskStatusCode.Completed
    assert task.result() == mock_result
    assert task._result_exists()
    assert task == task.fetch()

    task.cancel()
    assert backend.cancel_task.call_count == 1


def test_serializer():
    prog = (
        start.add_position((0, 0))
        .rydberg.detuning.uniform.piecewise_linear(
            [0.1, 0.5, 0.1], [1.0, 2.0, 3.0, 4.0]
        )
        .constant(4.0, 1)
    )

    for backend in [
        "braket.aquila",
        "braket.local_emulator",
        "bloqade.python",
        "quera.aquila",
    ]:
        print(backend)
        batch = prog.device(backend)._compile(10)

        json_str = dumps(batch, use_decimal=True)
        new_batch = loads(json_str, use_decimal=True)
        for task_num, task in batch.tasks.items():
            if hasattr(task, "emulator_ir"):
                assert task.emulator_ir == new_batch.tasks[task_num].emulator_ir
            else:
                assert task.task_ir == new_batch.tasks[task_num].task_ir
            assert task.metadata == new_batch.tasks[task_num].metadata
            assert task.task_result_ir == new_batch.tasks[task_num].task_result_ir
            assert task.nshots == new_batch.tasks[task_num].nshots
