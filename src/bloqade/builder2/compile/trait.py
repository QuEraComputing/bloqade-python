from ... import ir
from .ir import SequenceCompiler, RegisterCompiler
from .json import BuilderSerializer
from ...codegen.common.static_assign import StaticAssignProgram
from typing import Union
import json


class CompileJSON:
    def json(self, **json_options) -> str:
        return json.dumps(self, cls=BuilderSerializer, **json_options)

    def __repr__(self):
        raise NotImplementedError


class CompileRegister:
    def compile_register(self) -> Union[ir.AtomArrangement, ir.ParallelRegister]:
        return RegisterCompiler(self).compile()


class CompileSequence:
    def compile_sequence(self):
        return SequenceCompiler(self).compile()


class CompileProgram(CompileRegister, CompileSequence):
    def compile_program(self) -> ir.Program:
        return ir.Program(self.compile_register(), self.compile_sequence())


class Compile(CompileProgram):
    def compile_bloqade_ir(self, **mapping):
        return StaticAssignProgram(mapping).emit(self.compile_program())
