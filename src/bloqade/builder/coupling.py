from bloqade.ir.control.pulse import detuning
from .base import Builder


class LevelCoupling(Builder):
    @property
    def detuning(self):
        """Pick the detuning field as coupling."""
        from .field import Detuning

        self.__build_cache__.field_name = detuning
        return Detuning(self)

    @property
    def rabi(self):
        """Pick the rabi field as coupling."""
        from .field import Rabi

        return Rabi(self)


class Rydberg(LevelCoupling):
    pass


class Hyperfine(LevelCoupling):
    pass
