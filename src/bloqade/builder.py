from typing import List
from .ir.prelude import *
from .task import *

class Builder:
    def __init__(self, sequence) -> None:
        self.sequence: Sequence = sequence


class CouplingLevelBuilder(Builder):
    def __init__(self, lattice, sequence=Sequence({})) -> None:
        super().__init__(sequence)
        self.lattice = lattice

    @property
    def detuning(self) -> "SpatialModulationBuilder":
        return SpatialModulationBuilder(DetuningBuilder(self))

    @property
    def rabi(self) -> "RabiBuilder":
        return RabiBuilder(self)

    def ir_object(self) -> LevelCoupling:
        raise NotImplementedError


class RydbergBuilder(CouplingLevelBuilder):
    def ir_object(self):
        return rydberg


class HyperfineBuilder(CouplingLevelBuilder):
    def ir_object(self):
        return hyperfine


class FieldBuilder(Builder):
    def __init__(self, coupling_level: "CouplingLevelBuilder") -> None:
        super().__init__(coupling_level.sequence)
        self.coupling_level = coupling_level
        self.name: FieldName | None = None


class DetuningBuilder(FieldBuilder):
    def __init__(self, coupling_level: CouplingLevelBuilder) -> None:
        super().__init__(coupling_level)
        self.name = FieldName.Detuning


class RabiBuilder(FieldBuilder):
    @property
    def amplitude(self) -> "SpatialModulationBuilder":
        self.name = FieldName.RabiFrequencyAmplitude
        return SpatialModulationBuilder(self)

    @property
    def phase(self) -> "SpatialModulationBuilder":
        self.name = FieldName.RabiFrequencyPhase
        return SpatialModulationBuilder(self)


class SpatialModulationBuilder(Builder):
    def __init__(self, field: "FieldBuilder") -> None:
        super().__init__(field.sequence)
        self.field = field

    @property
    def glob(self):
        return GlobalLocationBuilder(self)

    def location(self, label: int):
        return LocalLocationBuilder(self, label)


class LocationBuilder(Builder):
    def __init__(self, spatial_mod: SpatialModulationBuilder) -> None:
        super().__init__(spatial_mod.sequence)
        self.spatial_mod = spatial_mod

    def apply(
        self, waveform: Waveform
    ):  # forward to ApplyBuilder if only one location specified
        return ApplyBuilder(self)._apply(waveform)


class GlobalLocationBuilder(LocationBuilder):
    pass


class LocalLocationBuilder(LocationBuilder):
    def __init__(self, spatial_mod: SpatialModulationBuilder, label: int) -> None:
        super().__init__(spatial_mod)
        self.label: List[int] = [label]
        self._scale: List[Scalar] = [cast(1.0)]

    def scale(self, val) -> "LocalLocationBuilder":
        self._scale.pop()
        self._scale.append(val)
        return self

    def location(self, label: int) -> "LocalLocationBuilder":
        self.label.append(label)
        self._scale.append(cast(1.0))
        return self


class ApplyBuilder(Builder):  # terminator
    def __init__(self, location: LocationBuilder) -> None:
        super().__init__(location.sequence)
        self.location_builder: LocationBuilder = location
        # NOTE: the following are for convenience
        self.spatial_mod: SpatialModulationBuilder = location.spatial_mod
        self.field: FieldBuilder = location.spatial_mod.field
        self.coupling_level: CouplingLevelBuilder = (
            location.spatial_mod.field.coupling_level
        )
        self.lattice = self.spatial_mod.field.coupling_level.lattice

    def _apply(self, waveform) -> "ApplyBuilder":
        coupling_level = self.coupling_level.ir_object()
        field_name = self.field.name

        if isinstance(self.location_builder, GlobalLocationBuilder):
            spatial_mod = Global
        elif isinstance(self.location_builder, LocalLocationBuilder):
            scaled_locations = {}
            for loc, scal in zip(
                self.location_builder.label, self.location_builder._scale
            ):
                scaled_locations[loc] = scal
            spatial_mod = ScaledLocations(scaled_locations)
        else:  # None
            raise ValueError("unexpected spatial location")

        # NOTE: Pulse and Field is not frozen
        pulse = self.sequence.value.setdefault(coupling_level, Pulse({}))
        field = pulse.value.setdefault(field_name, Field({}))
        if spatial_mod in field.value:
            raise ValueError("this field spatial modulation is already specified")
        field.value[spatial_mod] = waveform
        return self

    @property
    def _program(self) -> Program:
        return Program(self.lattice, self.sequence)

    def braket(self, *args, **kwargs) -> BraketTask:
        return self._program.braket(*args, **kwargs)

    def quera(self, *args, **kwargs) -> QuEraTask:
        return self._program.quera(*args, **kwargs)

    def simu(self, *args, **kwargs) -> SimuTask:
        return self._program.simu(*args, **kwargs)

    # apply can go any previous builder
    # 1. coupling builder, these need to construct manully
    #   because we need to share sequence object
    @property
    def rydberg(self) -> RydbergBuilder:
        return RydbergBuilder(self.lattice, self.sequence)

    @property
    def hyperfine(self) -> HyperfineBuilder:
        return HyperfineBuilder(self.lattice, self.sequence)

    # 2. FieldBuilder
    @property
    def detuning(self) -> SpatialModulationBuilder:
        return self.coupling_level.detuning

    @property
    def rabi(self) -> RabiBuilder:
        return self.coupling_level.rabi

    # 3. RabiBuilder
    @property
    def amplitude(self) -> SpatialModulationBuilder:
        if not isinstance(self.field, RabiBuilder):
            raise ValueError("amplitude can only specified on rabi channel")
        return self.field.amplitude

    @property
    def phase(self) -> SpatialModulationBuilder:
        if not isinstance(self.field, RabiBuilder):
            raise ValueError("phase can only specified on rabi channel")
        return self.field.phase

    # 4. SpatialModulationBuilder
    @property
    def glob(self) -> GlobalLocationBuilder:
        if isinstance(self.location_builder, GlobalLocationBuilder):
            raise ValueError("global waveform already specified")
        return self.spatial_mod.glob

    def location(self, label: int) -> LocalLocationBuilder:
        return self.spatial_mod.location(label)
