from ... import ir
from ..base import Builder
from ..compile.trait import CompileProgram
from ...task2.batch import RemoteBatch, LocalBatch


class Backend(Builder, CompileProgram):
    def _compile_task(self, bloqade_ir: ir.Program, shots: int, **metadata):
        raise NotImplementedError(
            "Compilation not implemented for "
            f"'{self.__service_name__}.{self.__device_name__}'."
        )


class LocalBackend(Backend):
    def __call__(self, *args, shots: int = 1, name: str = None):
        compiler = CompileProgram()

        tasks = [
            self._compile_task(program, shots, **metadata)
            for metadata, program in compiler.compile_ir(*args)
        ]
        batch = LocalBatch(tasks, name)

        return batch


class RemoteBackend(Backend):
    def __call__(self, *args, shots: int = 1, name: str = None, shuffle: bool = False):
        batch = self.submit(*args, shots, name, shuffle)
        batch.pull()  # blocking
        return batch

    def submit(self, *args, shots: int = 1, name: str = None, shuffle: bool = False):
        tasks = [
            self._compile_task(program, shots, **metadata)
            for metadata, program in self.compile_ir(*args)
        ]
        batch = RemoteBatch(dict(zip(range(len(tasks)), tasks)), name)

        batch._submit(shuffle)

        return batch
