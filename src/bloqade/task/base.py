from .report import TaskReport


class Task:
    def submit(self) -> "TaskFuture":
        raise NotImplementedError


class TaskFuture:
    def report(self) -> "TaskReport":
        """generate the task report"""
        return TaskReport(self)
