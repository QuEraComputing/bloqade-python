from bloqade.codegen.hardware.quera import SchemaCodeGen
from bloqade.ir.batch import BloqadeBatch
from bloqade.submission.braket import BraketBackend

from collections import OrderedDict
from typing import TYPE_CHECKING, Optional
from dataclasses import dataclass

if TYPE_CHECKING:
    from bloqade.task.batch import RemoteBatch


@dataclass
class BraketCompiler:
    """Lower from BloqadeBatch to RemoteBatch of BraketTask."""

    batch: BloqadeBatch
    backend: BraketBackend  # backend is determined by device_arn

    def compile(self, shots, name: Optional[str]) -> "RemoteBatch":
        from bloqade.task.braket import BraketTask

        tasks = OrderedDict()
        capabilities = self.backend.get_capabilities()
        for task_number, bloqade_task in self.batch.tasks.items():
            metadata = {**bloqade_task.assingments, **self.batch.program.assignments}
            task_ir, parallel_decoder = SchemaCodeGen(capabilities=capabilities).emit(
                shots, bloqade_task.ast
            )

            task_ir = task_ir.discretize(capabilities)
            task = BraketTask(
                task_id=None,
                task_ir=task_ir,
                parallel_decoder=parallel_decoder,
                metadata=metadata,
                backend=self.backend,
                task_result_ir=None,
            )

            tasks[task_number] = task
