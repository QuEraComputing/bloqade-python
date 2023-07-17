from .base import Builder
from .spatial import SpatialModulation
from bloqade.ir.control.pulse import rabi


class Detuning(SpatialModulation):
    pass


class Rabi(Builder):
    @property
    def amplitude(self):
        """specify the amplitude of the rabi field."""
        self.__build_cache__.field_name = rabi.amplitude
        return Amplitude(self)

    @property
    def phase(self):
        """specify the phase of the rabi field."""
        self.__build_cache__.field_name = rabi.phase
        return Phase(self)


class Amplitude(SpatialModulation):
    pass


class Phase(SpatialModulation):
    pass
