from bloqade.builder.base import Builder

from bloqade.task.batch import RemoteBatch, LocalBatch
from typing import Any, Tuple
from numbers import Real

class Backend(Builder):
    pass


class LocalBackend(Backend):
    def run(
        self,
        shots: int,
        args: Tuple[Real, ...] = (),
        name: str | None = None,
        **kwargs,
    ):
        tasks = self.compile_tasks(shots, *args)

        batch = LocalBatch(dict(zip(range(len(tasks)), tasks)), name)

        # kwargs is the tuning params for integrators
        batch._run(**kwargs)

        return batch

    def __call__(
        self,
        *args: Tuple[Real, ...],
        shots: int = 1,
        name: str | None = None,
        **kwargs,
    ) -> Any:
        return self.run(shots, args, **kwargs)

    def compile_tasks(self, shots, *args):
        raise NotImplementedError


class RemoteBackend(Backend):
    def run(
        self,
        shots: int,
        args: Tuple[Real, ...] = (),
        name: str | None = None,
        shuffle: bool = False,
    ):
        batch = self.submit(shots, args, name, shuffle)
        batch.pull()  # blocking
        return batch

    def __call__(
        self,
        *args: Tuple[Real, ...],
        shots: int = 1,
        name: str | None = None,
        shuffle: bool = False,
    ) -> Any:
        return self.run(shots, args, name, shuffle)

    def compile_tasks(self, shots, *args):
        raise NotImplementedError

    def submit(
        self,
        shots: int,
        args: Tuple[Real, ...] = (),
        name: str = None,
        shuffle: bool = False,
    ):
        tasks = self.compile_tasks(shots, *args)

        batch = RemoteBatch(dict(zip(range(len(tasks)), tasks)), name)

        batch._submit(shuffle)

        return batch
