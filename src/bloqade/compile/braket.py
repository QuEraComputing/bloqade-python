from bloqade.codegen.common.static_assign import StaticAssignProgram
from bloqade.codegen.hardware.quera import SchemaCodeGen
from bloqade.ir.program import Program
from bloqade.submission.braket import BraketBackend
from pydantic.dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from bloqade.task.batch import RemoteBatch


@dataclass
class BraketBatchCompiler:
    program: Program
    backend: BraketBackend  # backend is determined by device_arn

    def compile(self, shots, args, name: Optional[str]) -> "RemoteBatch":
        from bloqade.task.braket import BraketTask

        params = self.program.parse_args(*args)
        static_params = {**params, **self.program.static_params}

        precompiled_program = StaticAssignProgram(static_params).visit(self.program)
        capabilities = self.backend.get_capabilities()

        tasks = []
        for batch_parmas in self.program.batch_params:
            metadata = {**batch_parmas, **params}
            task_ir, parallel_decoder = SchemaCodeGen(batch_parmas, capabilities).emit(
                shots, precompiled_program
            )

            task = BraketTask(
                task_id=None,
                task_ir=task_ir,
                parallel_decoder=parallel_decoder,
                metadata=metadata,
                backend=self.backend,
                task_result_ir=None,
            )

            tasks.append(task)

        return RemoteBatch(tasks, name)
