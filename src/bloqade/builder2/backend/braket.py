from bloqade.builder2.base import Builder
from .base import LocalBackend, RemoteBackend
from pydantic.dataclasses import dataclass
import bloqade.ir as ir
from bloqade.task2.braket import BraketTask
from bloqade.task2.braket_simulator import BraketEmulatorTask
from bloqade.submission.braket import BraketBackend
from bloqade.submission.ir.braket import to_braket_task_ir
from braket.analog_hamiltonian_simulator.rydberg.constants import (
    RYDBERG_INTERACTION_COEF,
)


class BraketService(Builder):
    @property
    def braket(self):
        return BraketDeviceRoute(self)


class BraketDeviceRoute(Builder):
    def aquila(self) -> "Aquila":
        return Aquila(self)

    def simu(self) -> "Simu":
        return Simu(self)


class Aquila(RemoteBackend):
    __service_name__ = "braket"
    __device_name__ = "aquila"

    def __init__(self, parent: Builder | None = None) -> None:
        super().__init__(parent)

    def _compile_task(self, bloqade_ir: ir.Program, shots: int, **metadata):
        backend = BraketBackend()
        from bloqade.codegen.hardware.quera import SchemaCodeGen

        capabilities = backend.get_capabilities()
        schema_compiler = SchemaCodeGen([], capabilities=capabilities)
        task_ir = schema_compiler.emit(shots, self.program)
        task_ir = task_ir.discretize(capabilities)
        return BraketTask(
            task_ir=task_ir,
            backend=backend,
            parallel_decoder=schema_compiler.parallel_decoder,
        )


@dataclass
class SimuOptions:
    steps: int = (1000,)
    rydberg_interaction_coef: float = (RYDBERG_INTERACTION_COEF,)
    blockade_radius: float = (0.0,)
    progress_bar: bool = (False,)
    atol: float = (1e-8,)
    rtol: float = (1e-6,)
    solver_method: str = ("adams",)
    order: int = (12,)
    nsteps: int = (1000,)
    first_step: int = (0,)
    max_step: int = (0,)
    min_step: int = (0,)


class Simu(LocalBackend):
    __service_name__ = "braket"
    __device_name__ = "simu"

    def __init__(
        self,
        steps: int = 1000,
        rydberg_interaction_coef: float = RYDBERG_INTERACTION_COEF,
        blockade_radius: float = 0.0,
        progress_bar: bool = False,
        atol: float = 1e-8,
        rtol: float = 1e-6,
        solver_method: str = "adams",
        order: int = 12,
        nsteps: int = 1000,
        first_step: int = 0,
        max_step: int = 0,
        min_step: int = 0,
        parent: Builder | None = None,
    ) -> None:
        super().__init__(parent)
        self._local_emulator_options = SimuOptions(
            steps,
            rydberg_interaction_coef,
            blockade_radius,
            progress_bar,
            atol,
            rtol,
            solver_method,
            order,
            nsteps,
            first_step,
            max_step,
            min_step,
        )

    def _compile_task(self, bloqade_ir: ir.Program, shots: int, **metadata):
        from bloqade.codegen.hardware.quera import SchemaCodeGen

        schema_compiler = SchemaCodeGen([])
        task_ir = schema_compiler.emit(shots, self.program)
        return BraketEmulatorTask(task_ir=to_braket_task_ir(task_ir))
