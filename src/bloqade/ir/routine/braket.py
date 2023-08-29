from collections import OrderedDict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Tuple
from numbers import Real

from bloqade.submission.braket import BraketBackend
from bloqade.task.batch import LocalBatch, RemoteBatch
from bloqade.task.braket_simulator import BraketEmulatorTask
from bloqade.task.braket import BraketTask


if TYPE_CHECKING:
    from bloqade.builder.base import Builder


@dataclass(frozen=True)
class BraketServiceOptions:
    source: "Builder"

    def aquila(self) -> "BraketHardwareRoutine":
        backend = BraketBackend(
            device_arn="arn:aws:braket:us-east-1::device/qpu/quera/Aquila"
        )
        return BraketHardwareRoutine(source=self.source, backend=backend)

    def local_emulator(self):
        return BraketLocalEmulatorRoutine(source=self.source)


@dataclass(frozen=True)
class BraketHardwareRoutine:
    source: "Builder"
    backend: BraketBackend

    def submit(
        self,
        shots: int,
        args: Tuple[Real, ...] = (),
        name: str | None = None,
        shuffle: bool = False,
        **kwargs,
    ) -> "RemoteBatch":
        ## fall passes here ###
        from bloqade.builder.parse.builder import Parser
        from bloqade.codegen.common.static_assign import StaticAssignProgram
        from bloqade.codegen.hardware.quera import QuEraCodeGen

        capabilities = self.backend.get_capabilities()

        circuit, params = Parser().parse(self.source)
        circuit = StaticAssignProgram(params.static_params).visit(circuit)

        tasks = OrderedDict()

        for task_number, batch_params in enumerate(params.batch_assignments(*args)):
            final_circuit = StaticAssignProgram(batch_params).visit(circuit)
            task_ir, parallel_decoder = QuEraCodeGen(capabilities=capabilities).emit(
                shots, final_circuit
            )

            task_ir = task_ir.discretize(capabilities)
            tasks[task_number] = BraketTask(
                None,
                self.backend,
                task_ir,
                batch_params,
                parallel_decoder,
                None,
            )

        batch = RemoteBatch(source=self.source, tasks=tasks, name=name)

        batch._submit(shuffle, **kwargs)

        return batch

    def run(
        self,
        shots: int,
        args: Tuple[Real, ...] = (),
        name: str | None = None,
        shuffle: bool = False,
        **kwargs,
    ) -> RemoteBatch:
        batch = self.submit(shots, args, name, shuffle, **kwargs)
        batch.pull()
        return batch

    def __call__(
        self,
        *args: Tuple[Real, ...],
        shots: int = 1,
        name: str | None = None,
        shuffle: bool = False,
        **kwargs,
    ):
        return self.run(shots, args, name, shuffle, **kwargs)


@dataclass(frozen=True)
class BraketLocalEmulatorRoutine:
    source: "Builder"

    def run(
        self, shots: int, args: Tuple[Real, ...] = (), name: str | None = None, **kwargs
    ) -> "LocalBatch":
        ## fall passes here ###
        from bloqade.ir import ParallelRegister
        from bloqade.builder.parse.builder import Parser
        from bloqade.codegen.common.static_assign import StaticAssignProgram
        from bloqade.codegen.hardware.quera import QuEraCodeGen
        from bloqade.submission.ir.braket import to_braket_task_ir

        circuit, params = Parser().parse(self.source)
        circuit = StaticAssignProgram(params.static_params).visit(circuit)

        if isinstance(circuit.register, ParallelRegister):
            raise NotImplementedError(
                "Parallelization of atom arrangements is not supported for "
                "local emulation."
            )

        tasks = OrderedDict()

        for task_number, batch_params in enumerate(params.batch_assignments(*args)):
            final_circuit = StaticAssignProgram(batch_params).visit(circuit)
            quera_task_ir, _ = QuEraCodeGen().emit(shots, final_circuit)

            task_ir = to_braket_task_ir(quera_task_ir)

            tasks[task_number] = BraketEmulatorTask(
                task_ir,
                batch_params,
                None,
            )

        batch = LocalBatch(source=self.source, tasks=tasks, name=name)
        batch._run(**kwargs)

        return batch
