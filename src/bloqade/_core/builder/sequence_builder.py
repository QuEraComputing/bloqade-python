from bloqade._core.ir.control.sequence import SequenceExpr
from bloqade._core.builder.route import PragmaRoute
from bloqade._core.builder.base import Builder


class SequenceBuilder(PragmaRoute, Builder):
    def __init__(self, sequence: SequenceExpr, parent: Builder):
        super().__init__(parent)
        self._sequence = sequence
