from .base import Builder
from .coupling import Rydberg, Hyperfine
import bloqade.ir.control.sequence as SequenceExpr
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .emit import Emit


class ProgramStart(Builder):
    @property
    def rydberg(self):
        return Rydberg(self)

    @property
    def hyperfine(self):
        return Hyperfine(self)

    def apply(self, sequence: SequenceExpr) -> "Emit":
        from .emit import Emit

        if getattr(self, "__sequence__", None) is not None:
            raise NotImplementedError("Cannot apply multiple sequences")

        return Emit(self, register=self.__register__, sequence=sequence)
