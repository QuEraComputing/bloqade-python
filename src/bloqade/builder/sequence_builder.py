from bloqade.ir.control.sequence import Sequence
from bloqade.builder.route import PragmaRoute
from bloqade.builder.base import Builder


class SequenceBuilder(PragmaRoute, Builder):
    __match_args__ = ("_sequence", "__parent__")

    def __init__(self, sequence: Sequence, parent: Builder):
        super().__init__(parent)
        self._sequence = sequence
