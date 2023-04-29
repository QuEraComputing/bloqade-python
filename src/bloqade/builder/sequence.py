from ..ir.sequence import rydberg, hyperfine
from .pulse import DetuningBuilder, RabiBuilder
from .field import SpatialModulationBuilder

class Builder:

    def __init__(self, lattice) -> None:
        self.lattice = lattice

    @property
    def detuning(self):
        SpatialModulationBuilder(DetuningBuilder(self))

    @property
    def rabi(self):
        return RabiBuilder(self)

class RydbergBuilder(Builder):
    level_coupling = rydberg

class HyperfineBuilder(Builder):
    level_coupling = hyperfine
