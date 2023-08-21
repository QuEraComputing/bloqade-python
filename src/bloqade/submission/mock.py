from bloqade.submission.base import SubmissionBackend

from bloqade.submission.ir.task_specification import (
    QuEraTaskSpecification,
)
from bloqade.submission.ir.task_results import (
    QuEraTaskResults,
    QuEraTaskStatusCode,
    QuEraShotResult,
    QuEraShotStatusCode,
)
import uuid
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
    state_file: str = ".mock_state.txt"

    def submit_task(self, task: QuEraTaskSpecification) -> str:
        task_id = str(uuid.uuid4())
        task_results = simulate_task_results(task)
        with open(self.state_file, "a") as IO:
            IO.write(f"('{task_id}',{task_results.json()})\n")

        return task_id

    def task_results(self, task_id: str) -> QuEraTaskResults:
        # lazily search database for task_id
        for line in open(self.state_file, "r"):
            potential_task_id, task_results = eval(line)

            if potential_task_id == task_id:
                return QuEraTaskResults(**task_results)

        raise ValueError(f"unable to fetch results for task_id: {task_id}")

    def cancel_task(self, task_id: str):
        pass

    def task_status(self, task_id: str) -> QuEraTaskStatusCode:
        return QuEraTaskStatusCode.Completed
