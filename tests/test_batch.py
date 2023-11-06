from bloqade import start, load, save
import numpy as np
from unittest.mock import patch
from bloqade.submission.ir.task_results import QuEraTaskStatusCode, QuEraTaskResults

# import numpy as np


def mock_results_json():
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


def mock_results():
    return QuEraTaskResults(**mock_results_json())


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

    backend.task_results.return_value = mock_results()

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


def test_serializer():
    batch = (
        start.add_position((0, 0))
        .rydberg.detuning.uniform.piecewise_linear(
            [0.1, 0.5, 0.1], [1.0, 2.0, 3.0, 4.0]
        )
        .constant(4.0, 1)
        .braket.local_emulator()
        .run(1)
    )

    save(batch, "test.json")
    new_batch = load("test.json")
    assert batch.tasks == new_batch.tasks
