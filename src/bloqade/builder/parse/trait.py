from typing import Tuple, Union, TYPE_CHECKING
import json
import bloqade.ir as ir
from bloqade.visualization import display_builder


if TYPE_CHECKING:
    from bloqade.ir import AtomArrangement, ParallelRegister, Sequence
    from bloqade.ir.analog_circuit import AnalogCircuit
    from bloqade.ir.routine.params import Params
    from bloqade.builder.base import Builder


class CompileJSON:
    def json(self: "Builder", **json_options) -> str:
        """transform the program to a JSON string."""
        from bloqade.builder.parse.json import BuilderSerializer

        return json.dumps(self, cls=BuilderSerializer, **json_options)

    # def __repr__(self):
    #     raise NotImplementedError


class ParseRegister:
    def parse_register(self: "Builder") -> Union["AtomArrangement", "ParallelRegister"]:
        """Parse the arrangement of atoms of the program."""
        from bloqade.builder.parse.builder import Parser

        return Parser().parse_register(self)


class ParseSequence:
    def parse_sequence(self: "Builder") -> "Sequence":
        """Parse the pulse sequence part of the program."""
        from bloqade.builder.parse.builder import Parser

        return Parser().parse_sequence(self)


class ParseCircuit:
    def parse_circuit(self: "Builder") -> "AnalogCircuit":
        """Parse the analog circuit from the program."""
        from bloqade.builder.parse.builder import Parser

        return Parser().parse_circuit(self)


class ParseRoutine:
    """Parse the program to return an AnalogCircuit as well as the parameters
    for the circuit.


    """

    def parse_source(self: "Builder") -> Tuple["AnalogCircuit", "Params"]:
        from bloqade.builder.parse.builder import Parser

        return Parser().parse_source(self)


class Parse(ParseRegister, ParseSequence, ParseCircuit, ParseRoutine):
    @property
    def n_atoms(self: "Builder"):
        """Return the number of atoms in the program."""
        from .builder import Parser

        register = Parser().parse_register(self)

        if isinstance(register, ir.location.ParallelRegister):
            return register._register.n_atoms
        else:
            return register.n_atoms

    def __str__(self: "Builder"):
        from .builder import Parser

        analog_circ, metas = Parser().parse_source(self)

        return str(analog_circ) + "\n---------------------\n" + str(metas)

    def show(self, batch_id: int = 0):
        display_builder(self, batch_id)
