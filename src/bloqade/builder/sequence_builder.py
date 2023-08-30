from bloqade.ir.control.sequence import Sequence
from bloqade.builder.route import PragmaRoute
from bloqade.builder.base import Builder


class SequenceBuilder(PragmaRoute):
    __match_args__ = ("sequence", "__parent__")

    def __init__(self, sequence: Sequence, parent: Builder):
        self.sequence = sequence
        self.__parent__ = parent
