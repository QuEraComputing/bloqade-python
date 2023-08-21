# from ... import ir
from ..base import Builder, ParamType

from bloqade.task.batch import RemoteBatch, LocalBatch
from typing import Tuple

# from ..compile.quera import QuEraSchemaCompiler


class Backend(Builder):
    pass


class LocalBackend(Backend):
    def __call__(
        self,
        shots: int = 1,
        args: Tuple[ParamType, ...] = (),
        name: str = None,
        **kwargs,
    ):
        tasks = self.compile_tasks(shots, *args)

        batch = LocalBatch(dict(zip(range(len(tasks)), tasks)), name)

        # kwargs is the tuning params for integrators
        batch._run(**kwargs)

        return batch

    def compile_tasks(self, shots, *args):
        raise NotImplementedError


class RemoteBackend(Backend):
    def __call__(self, *args, shots: int = 1, name: str = None, shuffle: bool = False):
        batch = self.submit(*args, shots, name, shuffle)
        batch.pull()  # blocking
        return batch

    def compile_tasks(self, shots, *args):
        raise NotImplementedError

    def submit(self, *args, shots: int = 1, name: str = None, shuffle: bool = False):
        tasks = self.compile_tasks(shots, *args)

        batch = RemoteBatch(dict(zip(range(len(tasks)), tasks)), name)

        batch._submit(shuffle)

        return batch
