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
    def compile_register(self) -> Union["ir.AtomArrangement", "ir.ParallelRegister"]:
        from .ir import Parser

        return Parser(self).read_register()


class ParseSequence:
    def compile_sequence(self) -> ir.Sequence:
        from .ir import Parser

        return Parser(self).read_sequeence()


class Parse(ParseRegister, ParseSequence):
    pass
