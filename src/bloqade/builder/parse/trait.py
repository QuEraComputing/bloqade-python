from typing import Tuple, Union, TYPE_CHECKING
import json
import bloqade.ir as ir

if TYPE_CHECKING:
    from bloqade.ir import AtomArrangement, ParallelRegister, Sequence
    from bloqade.ir.analog_circuit import AnalogCircuit
    from bloqade.ir.routine.params import Params
    from bloqade.builder.base import Builder


class CompileJSON:
    def json(self: "Builder", **json_options) -> str:
        from bloqade.builder.parse.json import BuilderSerializer

        return json.dumps(self, cls=BuilderSerializer, **json_options)

    # def __repr__(self):
    #     raise NotImplementedError


class ParseRegister:
    def parse_register(self: "Builder") -> Union["AtomArrangement", "ParallelRegister"]:
        from bloqade.builder.parse.builder import Parser

        return Parser().parse_register(self)


class ParseSequence:
    def parse_sequence(self: "Builder") -> "Sequence":
        from bloqade.builder.parse.builder import Parser

        return Parser().parse_sequence(self)


class ParseCircuit:
    def parse_circuit(self: "Builder") -> "AnalogCircuit":
        from bloqade.builder.parse.builder import Parser

        return Parser().parse_circuit(self)


class ParseRoutine:
    def parse_source(self: "Builder") -> Tuple["AnalogCircuit", "Params"]:
        from bloqade.builder.parse.builder import Parser

        return Parser().parse_source(self)


class Parse(ParseRegister, ParseSequence, ParseCircuit, ParseRoutine):
    @property
    def n_atoms(self: "Builder"):
        from .builder import Parser

        register = Parser().parse_register(self)

        if isinstance(register, ir.location.ParallelRegister):
            return register._register.n_atoms
        else:
            return register.n_atoms
