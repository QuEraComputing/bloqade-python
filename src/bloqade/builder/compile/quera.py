from .ir import BuilderCompiler
from ..base import Builder, ParamType
from ...submission.ir.capabilities import QuEraCapabilities
from ...submission.ir.task_specification import QuEraTaskSpecification
from ...submission.ir.parallel import ParallelDecoder
from ...codegen.hardware.quera import SchemaCodeGen
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class QuEraTaskData:
    task_ir: QuEraTaskSpecification
    metadata: Dict[str, ParamType]
    parallel_decoder: Optional[ParallelDecoder] = None


class QuEraSchemaCompiler:
    def __init__(self, builder: Builder, capabilities: QuEraCapabilities):
        self.capabilities = capabilities
        self.ir_compiler = BuilderCompiler(builder)

    def compile(self, shots, *args) -> List[QuEraTaskData]:
        quera_task_data_list = []
        for data in self.ir_compiler.compile_ir(*args):
            schema_compiler = SchemaCodeGen(data.metadata, self.capabilities)
            task_ir = schema_compiler.emit(shots, data.program)
            quera_task_data_list.append(
                QuEraTaskData(task_ir, data.metadata, schema_compiler.parallel_decoder)
            )

        return quera_task_data_list
