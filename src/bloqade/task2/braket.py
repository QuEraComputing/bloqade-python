from .base import TaskFuture


class BraketTask(TaskFuture):
    def __init__(self, braket, task_specification):
        self.braket = braket
        self.task_specification = task_specification

    def fetch(self):
        raise NotImplementedError

    @property
    def shots(self):
        return self.fetch().shots
