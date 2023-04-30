from typing import List, Union
from .ir.prelude import *
from .task import *


class Builder:
    def __init__(self, sequence_or_builder: Union[Sequence, "Builder"]) -> None:
        if isinstance(sequence_or_builder, Builder):
            self._sequence = sequence_or_builder._sequence
        elif isinstance(sequence_or_builder, Sequence):
            self._sequence: Sequence = sequence_or_builder
        else:
            raise ValueError("expect Sequence or Builder")

    @property
    def sequence(self):
        """access the current sequence (Sequence) object."""
        return self._sequence


class CouplingLevelBuilder(Builder):
    def __init__(self, lattice, sequence=Sequence({})) -> None:
        super().__init__(sequence)
        self._lattice = lattice

    @property
    def detuning(self) -> "SpatialModulationBuilder":
        """add detuning field to coupling level."""
        return SpatialModulationBuilder(DetuningBuilder(self))

    @property
    def rabi(self) -> "RabiBuilder":
        """add Rabi field (amplitude or phase) to coupling level."""
        return RabiBuilder(self)


class RydbergBuilder(CouplingLevelBuilder):
    pass


class HyperfineBuilder(CouplingLevelBuilder):
    pass


class FieldBuilder(Builder):
    def __init__(self, coupling_level: "CouplingLevelBuilder") -> None:
        super().__init__(coupling_level)
        self.coupling_level = coupling_level
        self.name: FieldName | None = None


class DetuningBuilder(FieldBuilder):
    def __init__(self, coupling_level: CouplingLevelBuilder) -> None:
        super().__init__(coupling_level)
        self.name = FieldName.Detuning


class RabiBuilder(FieldBuilder):
    @property
    def amplitude(self) -> "SpatialModulationBuilder":
        """specify pulse on Rabi frequency amplitude"""
        self.name = FieldName.RabiFrequencyAmplitude
        return SpatialModulationBuilder(self)

    @property
    def phase(self) -> "SpatialModulationBuilder":
        """specify pulse on Rabi frequency phase"""
        self.name = FieldName.RabiFrequencyPhase
        return SpatialModulationBuilder(self)


class SpatialModulationBuilder(Builder):
    def __init__(self, field: "FieldBuilder") -> None:
        super().__init__(field)
        self._field = field

    @property
    def glob(self):
        """specify global modulation of the field. The waveform
        will be applied uniformly to all locations in the lattice.
        """
        return GlobalLocationBuilder(self)

    def location(self, label: int):
        """specify location of the pulse in the lattice with a label."""
        return LocalLocationBuilder(self, label)


class LocationBuilder(Builder):
    def __init__(self, spatial_mod: SpatialModulationBuilder) -> None:
        super().__init__(spatial_mod)
        self._spatial_mod = spatial_mod

    def apply(
        self, waveform: Waveform
    ):  # forward to ApplyBuilder if only one location specified
        """apply the waveform to the current location, field and coupling level."""
        return ApplyBuilder(self)._apply(waveform)


class GlobalLocationBuilder(LocationBuilder):
    pass


class LocalLocationBuilder(LocationBuilder):
    def __init__(self, spatial_mod: SpatialModulationBuilder, label: int) -> None:
        super().__init__(spatial_mod)
        self._label: List[int] = [label]
        self._scale: List[Scalar] = [cast(1.0)]

    def scale(self, val) -> "LocalLocationBuilder":
        """scale the waveform at the current location."""
        self._scale.pop()
        self._scale.append(val)
        return self

    def location(self, label: int) -> "LocalLocationBuilder":
        """add another location that shares the same waveform."""
        self._label.append(label)
        self._scale.append(cast(1.0))
        return self


class ApplyBuilder(Builder):  # terminator
    def __init__(self, location: LocationBuilder) -> None:
        super().__init__(location)
        self.__location_builder: LocationBuilder = location
        # NOTE: the following are for convenience
        self.__spatial_mod: SpatialModulationBuilder = location._spatial_mod
        self.__field: FieldBuilder = location._spatial_mod._field
        self.__coupling_level: CouplingLevelBuilder = (
            location._spatial_mod._field.coupling_level
        )
        self.__lattice = self.__spatial_mod._field.coupling_level._lattice

    def __coupling_object(self):
        if isinstance(self.__coupling_level, RydbergBuilder):
            return rydberg
        elif isinstance(self.__coupling_level, HyperfineBuilder):
            return hyperfine
        else:
            raise ValueError("unexpected coupling level")

    def _apply(self, waveform) -> "ApplyBuilder":
        coupling_level = self.__coupling_object()
        field_name = self.__field.name

        if isinstance(self.__location_builder, GlobalLocationBuilder):
            spatial_mod = Global
        elif isinstance(self.__location_builder, LocalLocationBuilder):
            scaled_locations = {}
            for loc, scal in zip(
                self.__location_builder._label, self.__location_builder._scale
            ):
                scaled_locations[loc] = scal
            spatial_mod = ScaledLocations(scaled_locations)
        else:  # None
            raise ValueError("unexpected spatial location")

        # NOTE: Pulse and Field is not frozen
        pulse = self._sequence.value.setdefault(coupling_level, Pulse({}))
        field = pulse.value.setdefault(field_name, Field({}))
        if spatial_mod in field.value:
            raise ValueError("this field spatial modulation is already specified")
        field.value[spatial_mod] = waveform
        return self

    @property
    def _program(self) -> Program:
        return Program(self.__lattice, self._sequence)

    def braket(self, *args, **kwargs) -> BraketTask:
        """finish building the pulse program, and submit to braket."""
        return self._program.braket(*args, **kwargs)

    def quera(self, *args, **kwargs) -> QuEraTask:
        """finish building the pulse program, and submit to QuEra."""
        return self._program.quera(*args, **kwargs)

    def simu(self, *args, **kwargs) -> SimuTask:
        """finish building the pulse program, and submit to local simulator."""
        return self._program.simu(*args, **kwargs)

    # apply can go any previous builder
    # 1. coupling builder, these need to construct manully
    #   because we need to share sequence object
    @property
    def rydberg(self) -> RydbergBuilder:
        """specify rydberg coupling level that is in separate
        from previous coupling level (hyperfine).
        """
        return RydbergBuilder(self.__lattice, self._sequence)

    @property
    def hyperfine(self) -> HyperfineBuilder:
        """specify hyperfine coupling level that is in separate
        from previous coupling level (rydberg).
        """
        return HyperfineBuilder(self.__lattice, self._sequence)

    # 2. FieldBuilder
    @property
    def detuning(self) -> SpatialModulationBuilder:
        """specify a new detuning field on the current coupling level."""
        return self.__coupling_level.detuning

    @property
    def rabi(self) -> RabiBuilder:
        """specify a new rabi field on the current coupling level."""
        return self.__coupling_level.rabi

    # 3. RabiBuilder
    @property
    def amplitude(self) -> SpatialModulationBuilder:
        """specify a new amplitude modulation on the current rabi field."""
        if not isinstance(self.__field, RabiBuilder):
            raise ValueError("amplitude can only specified on rabi channel")
        return self.__field.amplitude

    @property
    def phase(self) -> SpatialModulationBuilder:
        """specify a new phase modulation on the current rabi field."""
        if not isinstance(self.__field, RabiBuilder):
            raise ValueError("phase can only specified on rabi channel")
        return self.__field.phase

    # 4. SpatialModulationBuilder
    @property
    def glob(self) -> GlobalLocationBuilder:
        """create a global location under the current field and coupling level."""
        if isinstance(self.__location_builder, GlobalLocationBuilder):
            raise ValueError("global waveform already specified")
        return self.__spatial_mod.glob

    def location(self, label: int) -> LocalLocationBuilder:
        """create a new location under the current field and coupling level."""
        return self.__spatial_mod.location(label)
