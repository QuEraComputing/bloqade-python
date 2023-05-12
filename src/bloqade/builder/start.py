from .base import Builder
from .coupling import Rydberg, Hyperfine


class ProgramStart(Builder):
    @property
    def rydberg(self):
        return Rydberg(self)

    @property
    def hyperfine(self):
        return Hyperfine(self)
