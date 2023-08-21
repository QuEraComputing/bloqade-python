from .ir import BuilderCompiler
from ..base import Builder, ParamType
from ...codegen.hardware.quera import SchemaCodeGen
from typing import Dict, List
from dataclasses import dataclass
from bloqade.submission.ir.braket import BraketTaskSpecification, to_braket_task_ir


@dataclass
class BraketEmulatorTaskData:
    task_ir: BraketTaskSpecification
    metadata: Dict[str, ParamType]
    # parallel_decoder: Optional[ParallelDecoder] = None


class BraketEimulatorCompiler:
    def __init__(self, builder: Builder):
        self.ir_compiler = BuilderCompiler(builder)

    def compile(self, shots, *args) -> List[BraketEmulatorTaskData]:
        quera_task_data_list = []
        for data in self.ir_compiler.compile_ir(*args):
            schema_compiler = SchemaCodeGen({})
            task_ir = schema_compiler.emit(shots, data.program)
            quera_task_data_list.append(
                BraketEmulatorTaskData(to_braket_task_ir(task_ir), data.metadata)
            )

        return quera_task_data_list
