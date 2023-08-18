from ..ir.control.sequence import Sequence
from .route import PragmaRoute
from .base import Builder
from .compile.trait import CompileProgram


class SequenceBuilder(PragmaRoute, CompileProgram):
    __match_args__ = ("sequence", "__parent__")

    def __init__(self, sequence: Sequence, parent: Builder):
        self.sequence = sequence
        self.__parent__ = parent
