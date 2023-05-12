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
    pass


class Hyperfine(LevelCoupling):
    pass
