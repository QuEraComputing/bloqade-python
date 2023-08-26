from numbers import Real
from typing import Optional, Tuple
from bloqade.builder.base import Builder
from bloqade.builder.backend.base import LocalBackend, RemoteBackend
from bloqade.task.batch import LocalBatch, RemoteBatch

# import bloqade.ir as ir
# from bloqade.task.braket import BraketTask
# from bloqade.task.braket_simulator import BraketEmulatorTask
# import bloqade.submission.braket as braket_submit

# from bloqade.submission.ir.braket import to_braket_task_ir


class BraketService(Builder):
    @property
    def braket(self):
        return BraketDeviceRoute(self)


class BraketDeviceRoute(Builder):
    def aquila(self) -> "Aquila":
        return Aquila(parent=self)

    def local_emulator(self) -> "BraketEmulator":
        return BraketEmulator(parent=self)


class Aquila(RemoteBackend):
    __service_name__ = "braket"
    __device_name__ = "aquila"

    def __init__(
        self,
        # cache_compiled_programs: bool = False,
        parent: Builder | None = None,
    ) -> None:
        # super().__init__(cache_compiled_programs, parent=parent)
        super().__init__(parent=parent)

    def compile(
        self, shots: int, args: Tuple[Real, ...], name: str | None = None
    ) -> RemoteBatch:
        from bloqade.builder.parse.builder import Parser
        from bloqade.lower.batch import LowerBloqadeProgram
        from bloqade.lower.braket import BraketCompiler
        from bloqade.submission.braket import BraketBackend

        backend = BraketBackend(
            device_arn="arn:aws:braket:us-east-1::device/qpu/quera/Aquila"
        )

        program = Parser(self).parse()
        batch = LowerBloqadeProgram(program).compile(args)
        return BraketCompiler(batch, backend).compile(shots, name)


class BraketEmulator(LocalBackend):
    __service_name__ = "braket"
    __device_name__ = "local_emulator"

    def __init__(
        self,
        parent: Optional[Builder] = None,
    ) -> None:
        super().__init__(parent=parent)

    def compile(
        self, shots: int, args: Tuple[Real, ...], name: str | None = None
    ) -> LocalBatch:
        from bloqade.builder.parse.builder import Parser
        from bloqade.lower.batch import LowerBloqadeProgram
        from bloqade.lower.braket_simulator import CompileBraketEmulator

        program = Parser(self).parse()
        batch = LowerBloqadeProgram(program).compile(args)
        return CompileBraketEmulator(batch).compile(shots, name)
