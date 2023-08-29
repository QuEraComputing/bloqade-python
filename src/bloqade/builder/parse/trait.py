from typing import Tuple, Union, TYPE_CHECKING
import json
import bloqade.ir as ir

if TYPE_CHECKING:
    from bloqade.ir import AtomArrangement, ParallelRegister, Sequence
    from bloqade.ir.analog_circuit import AnalogCircuit
    from bloqade.ir.routine.params import Params


class CompileJSON:
    def json(self, **json_options) -> str:
        from bloqade.builder.parse.json import BuilderSerializer

        return json.dumps(self, cls=BuilderSerializer, **json_options)

    # def __repr__(self):
    #     raise NotImplementedError


class ParseRegister:
    def parse_register(self) -> Union["AtomArrangement", "ParallelRegister"]:
        from bloqade.builder.parse.builder import Parser

        return Parser().parse_register(self)


class ParseSequence:
    def parse_sequence(self) -> "Sequence":
        from bloqade.builder.parse.builder import Parser

        return Parser().parse_sequence(self)


class ParseProgram:
    def parse_program(self) -> Tuple["AnalogCircuit", "Params"]:
        from bloqade.builder.parse.builder import Parser

        return Parser().parse(self)


class Parse(ParseRegister, ParseSequence, ParseProgram):
    @property
    def n_atoms(self):
        from .builder import Parser

        ps = Parser().parse_register(self)

        if isinstance(ps.register, ir.location.ParallelRegister):
            return ps.register._register.n_atoms
        else:
            return ps.register.n_atoms
