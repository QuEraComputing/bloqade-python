from .base import Builder


class LevelCoupling(Builder):
    @property
    def detuning(self):
        from .field import Detuning

        return Detuning(self)

    @property
    def rabi(self):
        from .field import Rabi

        return Rabi(self)


class Rydberg(LevelCoupling):
    def __bloqade_ir__(self):
        from bloqade.ir.control.sequence import rydberg

        return rydberg


class Hyperfine(LevelCoupling):
    def __bloqade_ir__(self):
        from bloqade.ir.control.sequence import hyperfine

        return hyperfine
