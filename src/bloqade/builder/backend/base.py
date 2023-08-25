from bloqade.builder.base import Builder

from bloqade.task.batch import RemoteBatch, LocalBatch
from typing import Any, Optional, Tuple
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
        batch = self.compile(shots, args, name)

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

    def compile(
        self, shots: int, args: Tuple[Real, ...], name: Optional[str] = None
    ) -> LocalBatch:
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

    def compile(
        self, shots: int, args: Tuple[Real, ...], name: Optional[str] = None
    ) -> RemoteBatch:
        raise NotImplementedError

    def submit(
        self,
        shots: int,
        args: Tuple[Real, ...] = (),
        name: str = None,
        shuffle_submit_order: bool = False,
    ):
        batch = self.compile(shots, args, name)

        batch._submit(shuffle_submit_order=shuffle_submit_order)

        return batch
