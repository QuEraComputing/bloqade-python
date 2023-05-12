from .base import Builder
from .spatial import SpatialModulation


class Detuning(SpatialModulation):
    pass


class Rabi(Builder):
    @property
    def amplitude(self):
        return Amplitude(self)

    @property
    def phase(self):
        return Phase(self)


class Amplitude(SpatialModulation):
    pass


class Phase(SpatialModulation):
    pass
