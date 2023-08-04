from bloqade.submission.base import SubmissionBackend
import pytest


def test_submission_base():
    A = SubmissionBackend()

    with pytest.raises(NotImplementedError):
        A.cancel_task("1")

    with pytest.raises(NotImplementedError):
        A.task_results("1")

    with pytest.raises(NotImplementedError):
        A.task_status("1")
