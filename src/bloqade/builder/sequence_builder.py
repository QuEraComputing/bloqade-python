from ..ir.control.sequence import Sequence
from .route import PragmaRoute
from .base import Builder


class SequenceBuilder(PragmaRoute):
    __match_args__ = ("sequence", "__parent__")

    def __init__(self, sequence: Sequence, parent: Builder):
        self.sequence = sequence
        self.__parent__ = parent
