from bloqade.core.ir.control.sequence import SequenceExpr
from bloqade.core.builder.route import PragmaRoute
from bloqade.core.builder.base import Builder


class SequenceBuilder(PragmaRoute, Builder):
    def __init__(self, sequence: SequenceExpr, parent: Builder):
        super().__init__(parent)
        self._sequence = sequence
