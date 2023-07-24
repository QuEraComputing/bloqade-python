from .base import Builder
from .coupling import Rydberg, Hyperfine
import bloqade.ir.control.sequence as SequenceExpr
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .emit import Emit


class ProgramStart(Builder):
    """
    ProgramStart is the base class for a starting/entry node for building a program.
    """

    @property
    def rydberg(self):
        """
        Specify the Rydberg level coupling.
        See [`Rydberg`][bloqade.builder.coupling.Rydberg] for more details.
        """
        return Rydberg(self)

    @property
    def hyperfine(self):
        """
        Specify the Hyperfile level coupling.
        See [Hyperfine][bloqade.builder.coupling.Hyperfine] for more details.
        """
        return Hyperfine(self)

    def apply(self, sequence: SequenceExpr) -> "Emit":
        """apply an existing pulse sequence to the program."""
        from .emit import Emit

        if getattr(self, "__sequence__", None) is not None:
            raise NotImplementedError("Cannot apply multiple sequences")

        return Emit(self, register=self.__register__, sequence=sequence)
