from ... import ir
from typing import Union
import json


class CompileJSON:
    def json(self, **json_options) -> str:
        from .json import BuilderSerializer

        return json.dumps(self, cls=BuilderSerializer, **json_options)

    def __repr__(self):
        raise NotImplementedError


class CompileRegister:
    def compile_register(self) -> Union[ir.AtomArrangement, ir.ParallelRegister]:
        from .ir import RegisterCompiler

        return RegisterCompiler(self).compile()


class CompileSequence:
    def compile_sequence(self):
        from .ir import SequenceCompiler

        return SequenceCompiler(self).compile()


class CompileProgram(CompileRegister, CompileSequence):
    def compile_program(self) -> ir.Program:
        return ir.Program(self.compile_register(), self.compile_sequence())


class Compile(CompileProgram):
    def compile_bloqade_ir(self, **mapping):
        from ...codegen.common.static_assign import StaticAssignProgram

        return StaticAssignProgram(mapping).emit(self.compile_program())
