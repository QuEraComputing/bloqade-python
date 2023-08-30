from collections import OrderedDict
from bloqade.codegen.hardware.quera import QuEraCodeGen
from bloqade.ir.batch import TaskBatch
from bloqade.submission.quera import QuEraBackend
from bloqade.submission.mock import MockBackend
from typing import TYPE_CHECKING, Optional, Union
from dataclasses import dataclass

if TYPE_CHECKING:
    from bloqade.task.batch import RemoteBatch


@dataclass
class QuEraCompiler:
    """Lower from BloqadeBatch to RemoteBatch of QuEraTask."""

    batch: TaskBatch
    backend: Union[QuEraBackend, MockBackend]

    def compile(self, shots, name: Optional[str]) -> "RemoteBatch":
        from bloqade.task.quera import QuEraTask
        from bloqade.task.batch import RemoteBatch

        tasks = OrderedDict()
        capabilities = self.backend.get_capabilities()
        for task_number, bloqade_task in self.batch.tasks.items():
            metadata = {**bloqade_task.assingments, **self.batch.program.assignments}
            task_ir, parallel_decoder = QuEraCodeGen(capabilities=capabilities).emit(
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
