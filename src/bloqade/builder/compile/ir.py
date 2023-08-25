from dataclasses import dataclass
import bloqade.ir as ir

from bloqade.builder.base import Builder, ParamType
from typing import List, Dict


@dataclass
class ProgramData:
    program: ir.Program
    metadata: Dict[str, ParamType]


class BuilderCompiler:
    def __init__(self, builder: Builder) -> None:
        from bloqade.builder.compile.builder import Parser

        self.program = Parser(builder).parse()

    def compile_ir(self, *args) -> List[ProgramData]:
        from bloqade.codegen.common.static_assign import StaticAssignProgram

        arg_params = self.program.parse_args(*args)
        static_params = {**arg_params, **self.program.static_params}

        precompiled_program = StaticAssignProgram(static_params).visit(self.program)

        programs = []
        for params in self.program.batch_params:
            metadata = {**params, **arg_params}
            program = StaticAssignProgram(params).visit(precompiled_program)
            programs.append(ProgramData(program, metadata))

        return programs
