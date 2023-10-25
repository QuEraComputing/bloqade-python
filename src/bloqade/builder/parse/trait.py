from beartype.typing import Union, TYPE_CHECKING
import bloqade.ir as ir
from bloqade.visualization import display_builder


if TYPE_CHECKING:
    from bloqade.ir import AtomArrangement, ParallelRegister, Sequence
    from bloqade.ir.analog_circuit import AnalogCircuit
    from bloqade.ir.routine.base import Routine
    from bloqade.builder.base import Builder


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
    def parse(self: "Builder") -> "Routine":
        """Parse the program to return a Routine object."""
        from bloqade.builder.parse.builder import Parser

        return Parser().parse(self)


class Parse(ParseRegister, ParseSequence, ParseCircuit, ParseRoutine):
    @property
    def n_atoms(self: "Builder"):
        """Return the number of atoms in the program."""

        register = self.parse_register()

        if isinstance(register, ir.location.ParallelRegister):
            return register._register.n_atoms
        else:
            return register.n_atoms


class Show:
    def show(self, batch_id: int = 0):
        display_builder(self, batch_id)
