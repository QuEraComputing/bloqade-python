from .base import Builder
from bloqade.ir.control.sequence import Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .sequence_builder import SequenceBuilder


class ProgramStart(Builder):
    @property
    def rydberg(self):
        from .coupling import Rydberg

        return Rydberg(self)

    @property
    def hyperfine(self):
        from .coupling import Hyperfine

        return Hyperfine(self)

    def apply(self, sequence: Sequence) -> "SequenceBuilder":
        from .sequence_builder import SequenceBuilder

        return SequenceBuilder(self, sequence)
