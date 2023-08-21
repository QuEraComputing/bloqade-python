from bloqade.task.quera import QuEraTask
from bloqade.task.braket import BraketTask
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


#
# batch = RemoteBatch.from_json(...)
# batch.fetch() # update results,
#               # this is non-blocking.
#               # It only pull results if the remote job complete

# batch.pull() # this is blocking. it will hanging there waiting for job to complete.
# batch.to_json(...)

# # Get finished tasks (not nessasry sucessfully completed)
# finished_batch = batch.get_finished_tasks()

# # Get complete tasks (sucessfully completed)
# completed_batch = batch.get_completed_tasks()

# # Remove failed tasks:
# new_batch = batch.remove_failed_tasks()
