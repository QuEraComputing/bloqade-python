from collections import OrderedDict
from bloqade.codegen.hardware.quera import SchemaCodeGen
from bloqade.ir.batch import BloqadeBatch
from bloqade.submission.quera import QuEraBackend
from bloqade.submission.mock import DumbMockBackend
from typing import TYPE_CHECKING, Optional, Union
from dataclasses import dataclass

if TYPE_CHECKING:
    from bloqade.task.batch import RemoteBatch


@dataclass
class QuEraCompiler:
    """Lower from BloqadeBatch to RemoteBatch of QuEraTask."""

    batch: BloqadeBatch
    backend: Union[QuEraBackend, DumbMockBackend]

    def compile(self, shots, name: Optional[str]) -> "RemoteBatch":
        from bloqade.task.quera import QuEraTask
        from bloqade.task.batch import RemoteBatch

        tasks = OrderedDict()
        capabilities = self.backend.get_capabilities()
        for task_number, bloqade_task in self.batch.tasks.items():
            metadata = {**bloqade_task.assingments, **self.batch.program.assignments}
            task_ir, parallel_decoder = SchemaCodeGen(capabilities=capabilities).emit(
                shots, bloqade_task.ast
            )

            task_ir = task_ir.discretize(capabilities)
            task = QuEraTask(
                task_id=None,
                task_ir=task_ir,
                parallel_decoder=parallel_decoder,
                metadata=metadata,
                backend=self.backend,
                task_result_ir=None,
            )

            tasks[task_number] = task

        return RemoteBatch(self.batch, tasks, name)
