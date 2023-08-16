from bloqade.task2.quera import QuEraTask
from bloqade.task2.braket import BraketTask
from bloqade.submission.quera import QuEraBackend
from bloqade.submission.braket import BraketBackend
import pytest


def test_quera_task():
    backend = QuEraBackend(api_hostname="a", qpu_id="b")
    task = QuEraTask(task_ir=None, backend=backend)

    assert task._result_exists() is False

    with pytest.raises(ValueError):
        task.fetch()

    with pytest.raises(ValueError):
        task.pull()


def test_braket_task():
    backend = BraketBackend()
    task = BraketTask(task_ir=None, backend=backend)

    assert task._result_exists() is False

    with pytest.raises(ValueError):
        task.fetch()

    with pytest.raises(ValueError):
        task.pull()
