# report = lattice.Square(3)\
#     .rydberg.detuning.glob\
#         .apply(Linear(start=1.0, stop='x', duration=3.0))\
#     .location(1).scale(1.0)\
#         .apply(Linear(start=1.0, stop='x', duration=3.0))\
#     .braket(nshots=1000)\
#     .submit(token="wqnknlkwASdsq")\
#     .report()
from bloqade.builder import CouplingLevelBuilder
from typing import List
from .ir.prelude import *
from .ir.scalar import cast

class Builder:

    def __init__(self, sequence) -> None:
        self.sequence: dict = sequence

class CouplingLevelBuilder(Builder):

    def __init__(self, lattice, sequence={}) -> None:
        super().__init__(sequence)
        self.lattice = lattice

    @property
    def detuning(self):
        SpatialModulationBuilder(DetuningBuilder(self))

    @property
    def rabi(self):
        return RabiBuilder(self)

class RydbergBuilder(CouplingLevelBuilder):
    pass

class HyperfineBuilder(CouplingLevelBuilder):
    pass


class FieldBuilder(Builder):

    def __init__(self, coupling_level: "CouplingLevelBuilder") -> None:
        super().__init__(coupling_level.sequence)
        if isinstance(coupling_level, RydbergBuilder):
            self.coupling_level = rydberg
        elif isinstance(coupling_level, HyperfineBuilder):
            self.coupling_level = hyperfine
        else:
            raise ValueError('unsupported coupling level')
        self.lattice = coupling_level.lattice
        self.field_name = None

class DetuningBuilder(FieldBuilder):
    
    def __init__(self, coupling_level: CouplingLevelBuilder) -> None:
        super().__init__(coupling_level)
        self.field_name = FieldName.Detuning

class RabiBuilder(FieldBuilder):

    @property
    def amplitude(self) -> "SpatialModulation":
        self.field_name = FieldName.RabiFrequencyAmplitude
        return SpatialModulation(self)

    @property
    def phase(self) -> "SpatialModulation":
        self.field_name = FieldName.RabiFrequencyPhase
        return SpatialModulation(self)


class SpatialModulationBuilder(Builder):
    
    def __init__(self, field: "FieldBuilder") -> None:
        super().__init__(field.sequence)
        self.lattice = field.lattice
        self.coupling_level = field.coupling_level
        self.field_name = field.field_name
        self.location: None | Global | List[Location] = None
        self.scale: List[Scalar] = []

    @property
    def glob(self):
        self.location = Global
        return ApplyBuilder(self)

    @property
    def location(self, label: int):
        return LocationBuilder(self, label)

class LocationBuilder(Builder):

    def __init__(self, spatial_mod: SpatialModulationBuilder, label: int) -> None:
        super().__init__(spatial_mod.sequence)
        self.spatial_mod = spatial_mod
        self.spatial_mod.location = [Location(label)]
        self.spatial_mod.scale.append(cast(1.0))

    def scale(self, val):
        self.spatial_mod.scale.pop() # remove 1.0
        self.spatial_mod.scale.append(cast(val))
        return ApplyBuilder(self.spatial_mod)
    
    def location(self, label: int) -> "LocationBuilder":
        self.spatial_mod.location.append(Location(label))
        self.spatial_mod.scale.append(cast(1.0))
        return self

    def apply(self, waveform): # forward to ApplyBuilder if only one location specified
        return ApplyBuilder(self.spatial_mod).apply(waveform)



class ApplyBuilder(Builder): # terminator

    def __init__(self, spatial_mod: SpatialModulationBuilder) -> None:
        super().__init__(spatial_mod.sequence)
        self.coupling_level = spatial_mod.coupling_level
        self.field_name = spatial_mod.field_name
        self.location = spatial_mod.location
        self.scale = spatial_mod.scale
        self.lattice = spatial_mod.lattice

        if spatial_mod.location is Global:
            self.spatial_mod = Global
        elif isinstance(spatial_mod.location, list):
            scaled_locations = {}
            for loc, scal in zip(spatial_mod.location, spatial_mod.scale):
                scaled_locations[loc] = scal
            self.spatial_mod = ScaledLocations(scaled_locations)
        else: # None
            raise ValueError('unexpected spatial location, got None')

    def apply(self, waveform) -> "ApplyBuilder":
        field = self.sequence\
            .get(self.coupling_level, {})\
            .get(self.field_name, {})
        if self.spatial_mod in field:
            raise ValueError('this field location is already specified')
        field[self.spatial_mod] = waveform
        return self

    # apply can go any previous builder
    # 1. coupling builder
    @property
    def rydberg(self):
        return RydbergBuilder(self.lattice, self.sequence)
    
    @property
    def hyperfine(self):
        return HyperfineBuilder(self.lattice, self.sequence)
    
    # 2. 