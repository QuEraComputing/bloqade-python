from collections import OrderedDict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Tuple
from numbers import Real

from bloqade.submission.braket import BraketBackend


if TYPE_CHECKING:
    from bloqade.builder.base import Builder
    from bloqade.task.batch import RemoteBatch


@dataclass(frozen=True)
class BraketServiceOptions:
    source: "Builder"

    def aquila(self) -> "BraketHardwareRoutine":
        backend = BraketBackend(
            device_arn="arn:aws:braket:us-east-1::device/qpu/quera/Aquila"
        )
        return BraketHardwareRoutine(source=self.source, backend=backend)

    def local_emulator(self):
        pass


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
    ) -> RemoteBatch:
        ## fall passes here ###
        from bloqade.builder.parse.builder import Parser
        from bloqade.codegen.common.static_assign import StaticAssignProgram
        from bloqade.codegen.hardware.quera import QuEraCodeGen
        from bloqade.task.braket import BraketTask

        capabilities = self.backend.get_capabilities()

        circuit, params = Parser().parse(self.source)
        circuit = StaticAssignProgram(params.static_params).visit(circuit)

        tasks = OrderedDict()

        for task_number, params in enumerate(params.batch_assignments(*args)):
            task_ir, parallel_decoder = QuEraCodeGen(params, capabilities).emit(
                shots, circuit
            )
            tasks[task_number] = BraketTask(
                None,
                self.backend,
                task_ir,
                params,
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
    ):
        ## fall passes here ###
        from bloqade.builder.parse.builder import Parser
        from bloqade.codegen.common.static_assign import StaticAssignProgram
        from bloqade.codegen.hardware.quera import QuEraCodeGen
        from bloqade.submission.ir.braket import to_braket_task_ir
        from bloqade.task.braket_simulator import BraketEmulatorTask
        from bloqade.task.batch import LocalBatch

        capabilities = self.backend.get_capabilities()

        circuit, params = Parser().parse(self.source)
        circuit = StaticAssignProgram(params.static_params).visit(circuit)

        tasks = OrderedDict()

        for task_number, params in enumerate(params.batch_assignments(*args)):
            quera_task_ir, parallel_decoder = QuEraCodeGen(params, capabilities).emit(
                shots, circuit
            )

            task_ir = to_braket_task_ir(quera_task_ir)

            tasks[task_number] = BraketEmulatorTask(
                task_ir,
                params,
                None,
            )

        batch = LocalBatch(source=self.source, tasks=tasks, name=name)
        batch._run(**kwargs)

        return batch
