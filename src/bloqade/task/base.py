from .report import TaskReport, BatchReport
from bloqade.submission.quera_api_client.ir.task_results import QuEraTaskResults
from typing import List


class Task:
    def submit(self) -> "TaskFuture":
        raise NotImplementedError


class TaskFuture:
    def report(self) -> TaskReport:
        """generate the task report"""
        return TaskReport(self)

    def fetch(self) -> QuEraTaskResults:
        raise NotImplementedError

    @property
    def task_result(self):
        if self.task_result_ir:
            return self.task_result_ir

        self.task_result_ir = self.fetch()
        return self.task_result_ir


class Batch:
    def submit(self) -> "BatchFuture":
        raise NotImplementedError


class BatchFuture:
    def report(self) -> BatchReport:
        return BatchReport(self)

    def fetch(self) -> List[QuEraTaskResults]:
        raise NotImplementedError
