from bloqade.codegen.hardware.quera import SchemaCodeGen
from bloqade.submission.ir.braket import to_braket_task_ir
from bloqade.task.braket_simulator import BraketEmulatorTask
from bloqade.task.batch import LocalBatch
from bloqade.ir.batch import BloqadeBatch
from bloqade.ir.location.base import ParallelRegister

from collections import OrderedDict
from typing import Optional


class CompileBraketEmulator:
    """Lower from BloqadeBatch to LocalBatch of BraketEmulatorTask."""

    def __init__(self, batch: BloqadeBatch):
        self.batch = batch

    def compile(self, shots: int, name: Optional[str] = None) -> LocalBatch:
        if isinstance(self.batch.program.circuit.register, ParallelRegister):
            raise TypeError(
                "Braket local emulator does not support parallel registers."
            )

        tasks = OrderedDict()
        for task_number, task in self.batch.tasks.items():
            metadata = {**task.assingments, **self.batch.program.assignments}

            quera_task_ir, _ = SchemaCodeGen().emit(shots, task.ast)

            task = BraketEmulatorTask(
                task_ir=to_braket_task_ir(quera_task_ir),
                metadata=metadata,
                task_result_ir=None,
            )

            tasks[task_number] = task

        return LocalBatch(self.batch, tasks, name)
