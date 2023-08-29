from typing import Union, TYPE_CHECKING
import json

if TYPE_CHECKING:
    from bloqade.ir.program import Routine
    from bloqade.ir import AtomArrangement, ParallelRegister, Sequence


class CompileJSON:
    def json(self, **json_options) -> str:
        from bloqade.builder.parse.json import BuilderSerializer

        return json.dumps(self, cls=BuilderSerializer, **json_options)

    # def __repr__(self):
    #     raise NotImplementedError


class ParseRegister:
    def parse_register(self) -> Union["AtomArrangement", "ParallelRegister"]:
        from bloqade.builder.parse.builder import Parser

        return Parser(self).read_register()


class ParseSequence:
    def parse_sequence(self) -> "Sequence":
        from bloqade.builder.parse.builder import Parser

        return Parser(self).read_sequeence()


class ParseProgram:
    def parse_program(self) -> "Routine":
        from bloqade.builder.parse.builder import Parser

        return Parser(self).parse()


class Parse(ParseRegister, ParseSequence, ParseProgram):
    pass
