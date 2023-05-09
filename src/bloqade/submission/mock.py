from bloqade.submission.base import SubmissionBackend

from quera_ahs_utils.quera_ir.task_specification import QuEraTaskSpecification
from quera_ahs_utils.quera_ir.task_results import (
    QuEraTaskResults,
    QuEraTaskStatusCode,
    QuEraShotResult,
    QuEraShotStatusCode,
)
import uuid
import logging
import os
import numpy as np


def simulate_task_results(task: QuEraTaskSpecification, p_full=0.99, p_empty=0.01):
    natoms = len(task.lattice.sites)
    filling = task.lattice.filling

    pre_sequence_probs = np.array(
        [p_full if fill == 1 else p_empty for fill in filling]
    )
    post_sequence_probs = np.array(natoms * [0.5])

    rng = np.random.default_rng()

    shot_outputs = []
    for shot in range(task.nshots):
        pre_sequence = rng.binomial(np.ones(natoms, dtype=int), pre_sequence_probs)
        post_sequence = rng.binomial(
            np.ones(natoms, dtype=int), pre_sequence * post_sequence_probs
        )

        shot_outputs.append(
            QuEraShotResult(
                shot_status=QuEraShotStatusCode.Completed,
                pre_sequence=list(pre_sequence),
                post_sequence=list(post_sequence),
            )
        )

    return QuEraTaskResults(
        task_status=QuEraTaskStatusCode.Completed, shot_outputs=shot_outputs
    )


class DumbMockBackend(SubmissionBackend):
    def __init__(self, state_file=".mock_state.txt"):
        self.state_file = state_file
        self.state = {}
        if os.path.isfile(state_file):
            with open(state_file, "r") as IO:
                for line in IO:
                    task_id, task_json = eval(line)
                    self.state[task_id] = QuEraTaskResults(**task_json)

        self.logger = logging.getLogger(self.__class__.__name__)

    def submit_task(self, task: QuEraTaskSpecification) -> str:
        self.logger.debug("submitting task")
        task_id = str(uuid.uuid4())
        task_results = simulate_task_results(task)
        self.state[task_id] = task_results
        with open(self.state_file, "a") as IO:
            IO.write(f"('{task_id}',{task_results.json()})\n")
        self.logger.debug(f"task submitted with task_id: {task_id}")
        return task_id

    def task_results(self, task_id: str) -> QuEraTaskResults:
        try:
            task = self.state[task_id]
        except KeyError:
            raise ValueError(f"task_id {task_id}, not found.")
        return task

    def cancel_task(self, task_id: str):
        pass
