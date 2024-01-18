# from numbers import Real
from bloqade.visualization import display_ir
from bloqade.ir.control.sequence import SequenceExpr
from bloqade.ir.location.location import AtomArrangement, ParallelRegister
from bloqade.ir.tree_print import Printer
from beartype.typing import Union
from pydantic.dataclasses import dataclass


# NOTE: this is just a dummy type bundle geometry and sequence
#       information together and forward them to backends.
@dataclass(frozen=True)
class AnalogCircuit:
    """AnalogCircuit is a dummy type that bundle register and sequence together."""

    atom_arrangement: Union[ParallelRegister, AtomArrangement]
    sequence: SequenceExpr

    @property
    def register(self):
        """Get the register of the program.

        Returns:
            register (Union["AtomArrangement", "ParallelRegister"])

        Note:
            If the program is built with
            [`parallelize()`][bloqade.builder.emit.Emit.parallelize],
            The the register will be a
            [`ParallelRegister`][bloqade.ir.location.base.ParallelRegister].
            Otherwise it will be a
            [`AtomArrangement`][bloqade.ir.location.base.AtomArrangement].
        """
        return self.atom_arrangement

    def __eq__(self, other):
        if isinstance(other, AnalogCircuit):
            return (self.register == other.register) and (
                self.sequence == other.sequence
            )

        return False

    def __str__(self):
        out = ""
        if self.register is not None:
            out += self.register.__str__()

        out += "\n"

        if self.sequence is not None:
            out += self.sequence.__str__()

        return out

    def print_node(self):
        return "AnalogCircuit"

    def children(self):
        return {"register": self.atom_arrangement, "sequence": self.sequence}

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)

    def figure(self, **assignments):
        fig_reg = self.register.figure(**assignments)
        fig_seq = self.sequence.figure(**assignments)
        return fig_seq, fig_reg

    def show(self, **assignments):
        """Interactive visualization of the program

        Args:
            **assignments: assigning the instance value (literal) to the
                existing variables in the program

        """
        display_ir(self, assignments)
