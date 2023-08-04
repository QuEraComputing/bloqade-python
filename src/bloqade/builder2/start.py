from .base import Builder


class ProgramStart(Builder):
    @property
    def rydberg(self):
        from .coupling import Rydberg

        return Rydberg(self)

    @property
    def hyperfine(self):
        from .coupling import Hyperfine

        return Hyperfine(self)
