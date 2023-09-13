from bloqade.builder.base import Builder
from bloqade.builder.sequence_builder import SequenceBuilder
from bloqade.builder.drive import Drive
from bloqade.ir.control.sequence import Sequence
from beartype import beartype


class ProgramStart(Drive, Builder):
    """
    ProgramStart is the base class for a starting/entry node for building a program.
    """

    @beartype
    def apply(self, sequence: Sequence) -> SequenceBuilder:
        """apply an existing pulse sequence to the program."""
        return SequenceBuilder(sequence, self)
