from bloqade import start, load, save
import numpy as np
from unittest.mock import patch
import bloqade.ir.routine.braket

# import numpy as np


@patch("bloqade.ir.routine.braket.BraketBackend")
def test_remote_batch_task_metric(*args):
    backend = bloqade.ir.routine.braket.BraketBackend(
        device_arn="arn:aws:braket:us-east-1::device/qpu/quera/Aquila"
    )

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

    batch._submit(ignore_submission_error=True, shuffle_submit_order=False)

    assert str(batch) == (
        "  task ID    status  shots\n"
        "0       0  Enqueued     10\n"
        "1       1  Enqueued     10\n"
        "2       2  Enqueued     10\n"
        "3       3  Enqueued     10\n"
        "4       4  Enqueued     10\n"
        "5       5  Enqueued     10"
    )


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
