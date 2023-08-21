# from ... import ir
from ..base import Builder, ParamType

# from ...task2.batch import RemoteBatch, LocalBatch
from typing import Tuple

# from ..compile.quera import QuEraSchemaCompiler


class Backend(Builder):
    pass


class LocalBackend(Backend):
    def __call__(
        self, shots: int = 1, args: Tuple[ParamType, ...] = (), name: str = None
    ):
        raise NotImplementedError


class RemoteBackend(Backend):
    def __call__(self, *args, shots: int = 1, name: str = None, shuffle: bool = False):
        batch = self.submit(*args, shots, name, shuffle)
        batch.pull()  # blocking
        return batch

    def submit(self, *args, shots: int = 1, name: str = None, shuffle: bool = False):
        raise NotImplementedError
        # tasks = [
        #     QuEraTaskData(self._compile_task(program, shots, **metadata),metadata)
        #     for metadata, program in self.compile_ir(*args)
        # ]
        # batch = RemoteBatch(dict(zip(range(len(tasks)), tasks)), name)

        # batch._submit(shuffle)

        # return batch
