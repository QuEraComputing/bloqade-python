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

        return Emit(self, register=self.register, sequence=sequence)
