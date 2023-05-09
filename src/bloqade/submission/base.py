from bloqade.submission.ir import QuantumTaskIR


class SubmissionBackend:
    def submit_task(self, task_ir: QuantumTaskIR):
        raise NotImplementedError

    def cancel_task(self, task_id: str):
        raise NotImplementedError

    def task_results(self, task_id: str):
        raise NotImplementedError
