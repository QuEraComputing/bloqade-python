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


class Batch:
    def submit(self):
        raise NotImplementedError


class BatchFuture:
    def report(self) -> BatchReport:
        return BatchReport(self)

    def fetch(self) -> List[QuEraTaskResults]:
        raise NotImplementedError
