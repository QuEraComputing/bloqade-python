from collections import OrderedDict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Tuple
from numbers import Real

from bloqade.submission.braket import BraketBackend


if TYPE_CHECKING:
    from bloqade.ir.routine.base import Routine
    from bloqade.task.batch import RemoteBatch


@dataclass(frozen=True)
class BraketServiceOptions:
    parent_routine: "Routine"

    def Aquila(self) -> "AquilaRoutine":
        backend = BraketBackend(
            device_arn="arn:aws:braket:us-east-1::device/qpu/quera/Aquila"
        )
        return BraketRoutine(parent_routine=self.parent_routine, backend=backend)

    def local_emulator(self):
        pass


@dataclass(frozen=True)
class BraketRoutine:
    parent_routine: "Routine"

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

        source = self.parent_routine.source

        circuit, params = Parser().parse(source)
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

        batch = RemoteBatch(source=source, tasks=tasks, name=name)

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
class AquilaRoutine(BraketRoutine):
    backend: BraketBackend
    
    
@dataclass(frozen=True)
class BraketLocalEmulatorRoutine:
    def run(self, shots: int, args: Tuple[Real, ...]=(), **kwargs):
        ## fall passes here ###
        from bloqade.builder.parse.builder import Parser
        from bloqade.codegen.common.static_assign import StaticAssignProgram
        from bloqade.codegen.hardware.quera import QuEraCodeGen
        from bloqade.submission.ir.braket import to_braket_task_ir
        from bloqade.task.braket_simulator import BraketEmulatorTask
        from bloqade.task.batch import LocalBatch

        capabilities = self.backend.get_capabilities()

        source = self.parent_routine.source

        circuit, params = Parser().parse(source)
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

        batch = LocalBatch(source=source, tasks=tasks, name=name)

        batch._submit(shuffle, **kwargs)

        return batch
