from bloqade.atom_arrangement import Chain
from unittest.mock import patch
import bloqade.ir.routine.quera
from bloqade.task.batch import RemoteBatch
import glob
import os

import pytest


@patch("bloqade.ir.routine.quera.MockBackend")
def test_batch_error(*args):
    backend = bloqade.ir.routine.quera.MockBackend()

    backend.submit_task.side_effect = ValueError("some random error")
    backend.dict.return_value = {"state_file": ".mock_state.txt"}

    with pytest.raises(RemoteBatch.SubmissionException):
        (
            Chain(5, 6.1)
            .rydberg.detuning.uniform.linear(-10, 10, 3.0)
            .quera.mock()
            .run_async(100)
        )

    error_files = glob.glob("partial-batch-errors-*")
    batch_files = glob.glob("partial-batch-future-*")

    for error_file, batch_file in zip(error_files, batch_files):
        os.remove(error_file)
        os.remove(batch_file)

    assert len(error_files) == 1
    assert len(batch_files) == 1


@patch("bloqade.ir.routine.quera.MockBackend")
def test_batch_warn(*args):
    backend = bloqade.ir.routine.quera.MockBackend()

    backend.submit_task.side_effect = ValueError("some random error")
    backend.dict.return_value = {"state_file": ".mock_state.txt"}

    with pytest.warns():
        (
            Chain(5, 6.1)
            .rydberg.detuning.uniform.linear(-10, 10, 3.0)
            .quera.mock()
            .run_async(100, ignore_submission_error=True)
        )

    error_files = glob.glob("partial-batch-errors-*")
    batch_files = glob.glob("partial-batch-future-*")

    for error_file, batch_file in zip(error_files, batch_files):
        os.remove(error_file)
        os.remove(batch_file)

    assert len(error_files) == 1
    assert len(batch_files) == 1
