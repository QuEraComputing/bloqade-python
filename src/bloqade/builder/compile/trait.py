import bloqade.ir as ir
from typing import Union
import json


class CompileJSON:
    def json(self, **json_options) -> str:
        from bloqade.builder.compile.json import BuilderSerializer

        return json.dumps(self, cls=BuilderSerializer, **json_options)

    # def __repr__(self):
    #     raise NotImplementedError


class ParseRegister:
    def parse_register(self) -> Union["ir.AtomArrangement", "ir.ParallelRegister"]:
        from bloqade.builder.compile.builder import Parser

        return Parser(self).read_register()


class ParseSequence:
    def parse_sequence(self) -> ir.Sequence:
        from bloqade.builder.compile.builder import Parser

        return Parser(self).read_sequeence()


class ParseProgram:
    def parse_program(self) -> ir.Program:
        from bloqade.builder.compile.builder import Parser

        return Parser(self).parse()


class Parse(ParseRegister, ParseSequence, ParseProgram):
    pass
