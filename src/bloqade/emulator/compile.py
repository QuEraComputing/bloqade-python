import bloqade.ir.sequence as sequence
import bloqade.ir.pulse as pulse
import bloqade.ir.field as field
from bloqade.emulator.space import Space

from numpy.typing import NDArray
from typing import TYPE_CHECKING, Dict
from numbers import Number


if TYPE_CHECKING:
    from bloqade.lattice.base import Lattice


class Emulate:
    def __init__(self, psi: NDArray, space: Space, assignments: Dict[str, Number]):
        self.assignments = assignments
        self.psi = psi
        self.space = space

    def visit_lattice(self, ast: Lattice):
        # generate rydberg interaction.
        pass

    def visit_sequence(self, ast: sequence.SequenceExpr):
        match ast:
            case sequence.Sequence(pulses):
                self.visit(pulses)

            case sequence.Append(sequences):
                list(map(self.visit, sequences))

            case sequence.NamedSequence(sub_sequence, _):
                self.visit(sub_sequence)

            case _:
                raise NotImplementedError

    def visit_pulse(self, ast: pulse.PulseExpr):
        pass

    def visit_field(self, ast: field.Field):
        pass
