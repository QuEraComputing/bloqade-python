from ..ir.scalar import cast
from ..ir.field import Location, ScaledLocations, Global

class SpatialModulationBuilder:
    
    @property
    def glob(self):
        pass

    def location(self, label: int) -> "LocationBuilder":
        return LocationBuilder(self, label)


class LocationBuilder:
    
    def __init__(self, spatial_modulation: SpatialModulationBuilder, label: int) -> None:
        self.spatial_modulation = spatial_modulation
        self.location = Location(label)
        self._scale = cast(1.0)
 
    def scale(self, val):
        self._scale = cast(val)


class ApplyBuilder:

    def __init__(self, spatial_mod: SpatialModulationBuilder,  waveform) -> None:
        self.waveform = waveform

    def location(self, label: int) -> "LocationBuilder":
        LocationBuilder()

report = lattice.Square(3)\
    .rydberg.detuning.glob\
        .apply(Linear(start=1.0, stop='x', duration=3.0))\
    .location(1).scale(1.0)\
        .apply(Linear(start=1.0, stop='x', duration=3.0))\
    .braket(nshots=1000)\
    .submit(token="wqnknlkwASdsq")\
    .report()
