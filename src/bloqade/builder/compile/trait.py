from ... import ir
from typing import Union
import json


class CompileJSON:
    def json(self, **json_options) -> str:
        from .json import BuilderSerializer

        return json.dumps(self, cls=BuilderSerializer, **json_options)

    # def __repr__(self):
    #     raise NotImplementedError


class ParseRegister:
    def parse_register(self) -> Union["ir.AtomArrangement", "ir.ParallelRegister"]:
        from .builder import Parser

        return Parser(self).read_register()


class ParseSequence:
    def parse_sequence(self) -> ir.Sequence:
        from .builder import Parser

        return Parser(self).read_sequeence()


class ParseProgram:
    def parse_program(self) -> ir.Program:
        from .builder import Parser

        return Parser(self).parse()


class Parse(ParseRegister, ParseSequence, ParseProgram):
    @property
    def n_atoms(self):
        from .builder import Parser

        ps = Parser(self)
        ps.read_register()

        if isinstance(ps.register, ir.location.ParallelRegister):
            return ps.register._register.n_atoms
        else:
            return ps.register.n_atoms
