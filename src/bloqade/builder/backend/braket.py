from typing import Optional
from bloqade.builder2.base import Builder
from .base import LocalBackend, RemoteBackend
import bloqade.ir as ir
from bloqade.task2.braket import BraketTask
from bloqade.task2.braket_simulator import BraketEmulatorTask
import bloqade.submission.braket as braket_submit
from bloqade.submission.ir.braket import to_braket_task_ir


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
        self, cache_compiled_programs: bool = False, parent: Builder | None = None
    ) -> None:
        super().__init__(cache_compiled_programs, parent=parent)

    def _compile_task(self, bloqade_ir: ir.Program, shots: int, **metadata):
        from bloqade.codegen.hardware.quera import SchemaCodeGen

        backend = braket_submit.BraketBackend()

        capabilities = backend.get_capabilities()
        schema_compiler = SchemaCodeGen({}, capabilities=capabilities)
        task_ir = schema_compiler.emit(shots, bloqade_ir)
        task_ir = task_ir.discretize(capabilities)
        return BraketTask(
            task_ir=task_ir,
            backend=backend,
            parallel_decoder=schema_compiler.parallel_decoder,
        )


class BraketEmulator(LocalBackend):
    __service_name__ = "braket"
    __device_name__ = "local_emulator"

    def __init__(
        self,
        cache_compiled_programs: bool = False,
        parent: Optional[Builder] = None,
    ) -> None:
        super().__init__(cache_compiled_programs, parent=parent)

    def _compile_task(self, bloqade_ir: ir.Program, shots: int, **metadata):
        from bloqade.codegen.hardware.quera import SchemaCodeGen

        schema_compiler = SchemaCodeGen({})
        task_ir = schema_compiler.emit(shots, bloqade_ir)
        return BraketEmulatorTask(task_ir=to_braket_task_ir(task_ir))
