import bloqade.ir as ir
from typing import Union, Dict, List
from dataclasses import dataclass, field
from .task import Program, BraketTask, QuEraTask, SimuTask, MockTask


class BuildError(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)


@dataclass
class BuildCache:
    """A cache class for storing the current state of the builder."""

    skip_sequence_build: bool = False
    sequence: ir.Sequence = field(default_factory=ir.Sequence)
    assignments: Union[None, Dict[ir.Variable, ir.Literal]] = None
    program: Union[None, Program] = None
    # intermediate states that will be purge in Route
    waveform: Union[None, ir.Waveform] = None
    level_coupling: Union[None, ir.LevelCoupling] = None
    field_name: Union[None, ir.FieldName] = None
    locations: Union[None, List[int]] = None
    scales: Union[None, List[ir.Scalar]] = None
    spatial_mod: Union[None, ir.SpatialModulation] = None


class Builder:
    def __init__(self, parent: Union[ir.Sequence, "Builder", None] = None) -> None:
        # pass the cache from the parent builder
        if isinstance(parent, ir.Sequence):
            cache = BuildCache(sequence=parent)
            self.__lattice__ = None
        elif isinstance(parent, Builder):
            cache = parent.__cache__
            self.__lattice__ = parent.__lattice__
        elif parent is None:
            cache = BuildCache(sequence=ir.Sequence({}))
            self.__lattice__ = None
        else:
            raise ValueError("sequence_or_none must be a Sequence or None")

        # cache fields to pass over to the next builder
        self.__cache__ = cache


class Emit(Builder):
    def update_sequence(self) -> None:
        """update the internal sequence object with
        information stored in the current cache.
        """
        if self.__cache__.skip_sequence_build:
            return

        self.__validate_cache()
        if self.__cache__.spatial_mod:
            spatial_mod = self.__cache__.spatial_mod
        elif self.__cache__.locations:
            scaled_locations = {}
            for loc, scal in zip(self.__cache__.locations, self.__cache__.scales):
                scaled_locations[loc] = scal
            spatial_mod = ir.ScaledLocations(scaled_locations)
        else:
            raise BuildError(
                "spatial modulation must be set, can be set either using `.uniform`, \
`.var` or `.locations`"
            )

        seq = self.__cache__.sequence
        pulse: ir.Pulse = seq.value.setdefault(
            self.__cache__.level_coupling, ir.Pulse({})
        )
        field = pulse.value.setdefault(self.__cache__.field_name, ir.Field({}))
        if spatial_mod in field.value:
            raise BuildError("spatial modulation already exists")
        field.value[spatial_mod] = self.__cache__.waveform
        return self

    def __validate_cache(self) -> None:
        pass

    @property
    def program(self):
        self.update_sequence()
        return Program(
            self.__lattice__,
            self.__cache__.sequence,
            self.__cache__.assignments,
        )

    @property
    def sequence(self) -> ir.Sequence:
        """Return the current sequence object being built."""

        self.update_sequence()
        if self.__cache__.level_coupling is None:
            raise BuildError("level_coupling is not set")
        if self.__cache__.field_name is None:
            raise BuildError("field_name is not set")
        return self.__cache__.sequence

    @property
    def waveform(self) -> ir.Waveform:
        """Return the current waveform object being built."""
        return self.__cache__.waveform


class Assign(Builder):
    def assign(self, **kwargs) -> "Submit":
        if self.__cache__.assignments:
            raise ValueError(
                "assignments already exists, \
                can only call once for each builder pipeline"
            )
        self.__cache__.assignments = kwargs
        return Submit(self)


class Terminate(Builder):
    # build the IR object and return the terminated builder
    def apply(self, *args, **kwargs) -> "Route":
        raise NotImplementedError


# submit needs to make sure the sequence has been generated
class Submit(Emit):
    def braket(self, *args, **kwargs) -> BraketTask:
        return self.program.braket(*args, **kwargs)

    def quera(self, *args, **kwargs) -> QuEraTask:
        return self.program.quera(*args, **kwargs)

    def mock(self, nshots, state_file=".mock_state.txt") -> MockTask:
        return self.program.mock(nshots, state_file=state_file)

    def simu(self, *args, **kwargs) -> SimuTask:
        """finish building the pulse program, and submit to local simulator."""
        return self.program.simu(*args, **kwargs)


class LevelCouping(Builder):
    @property
    def rydberg(self):
        self.__cache__.level_coupling = ir.rydberg
        return Field(self)

    @property
    def hyperfine(self):
        self.__cache__.level_coupling = ir.hyperfine
        return Field(self)


class Field(Builder):
    @property
    def detuning(self):
        self.__cache__.field_name = ir.detuning
        return SpatialModulation(self)

    @property
    def rabi(self):
        return RabiBuilder(self)


class RabiBuilder(Field):
    @property
    def amplitude(self):
        self.__cache__.field_name = ir.rabi.amplitude
        return SpatialModulation(self)

    @property
    def phase(self):
        self.__cache__.field_name = ir.rabi.phase
        return SpatialModulation(self)


class Location(Builder):
    def location(self, label: int):
        if self.__cache__.locations:
            self.__cache__.locations.append(label)
            self.__cache__.scales.append(ir.cast(1.0))
        else:
            self.__cache__.locations = [label]
            self.__cache__.scales = [ir.cast(1.0)]
        return ScaleOrWaveform(self)


class SpatialModulation(Location):
    @property
    def uniform(self):
        self.__cache__.spatial_mod = ir.Uniform
        return WaveformOrTerminate(self)

    def var(self, name: str):
        """Variable spatial modulation."""
        self.__cache__.spatial_mod = ir.RunTimeVector(name)
        return WaveformOrTerminate(self)


class Waveform(Builder):
    def __update_waveform(self, wf: ir.Waveform) -> "Route":
        if self.__cache__.waveform:
            self.__cache__.waveform = self.__cache__.waveform.append(wf)
        else:
            self.__cache__.waveform = wf
        return Route(self)

    def linear(self, start, stop, duration):
        wf = ir.Linear(start, stop, duration)
        return self.__update_waveform(wf)

    def constant(self, value, duration):
        wf = ir.Constant(value, duration)
        return self.__update_waveform(wf)

    def poly(self, coefficients, duration):
        wf = ir.Poly(coefficients, duration)
        return self.__update_waveform(wf)


class WaveformCompose(Waveform):
    """Builder for building composite waveform"""

    def add(self, waveform: ir.Waveform):
        wf = self.__cache__.waveform + waveform
        return self.__update_waveform(wf)

    def append(self, waveform: ir.Waveform):
        wf = self.__cache__.waveform.append(waveform)
        return self.__update_waveform(wf)

    def scale(self, value):
        """scale the waveform."""
        wf = self.__cache__.waveform.scale(value)
        return self.__update_waveform(wf)

    def smooth(self, kernel="gaussian"):
        wf = self.__cache__.waveform.smooth(kernel)
        return self.__update_waveform(wf)

    def __getitem__(self, slice):
        wf = self.__cache__.waveform[slice]
        return self.__update_waveform(wf)


class AssignOrSubmit(Assign, Submit):
    pass


class Route(LevelCouping, Field, SpatialModulation, WaveformCompose, AssignOrSubmit):
    @property
    def rydberg(self):
        self.update_sequence()

        self.__cache__.skip_sequence_build = False
        self.__cache__.waveform = None
        self.__cache__.level_coupling = None
        self.__cache__.field_name = None
        self.__cache__.locations = None
        self.__cache__.scales = None
        self.__cache__.spatial_mod = None
        return super().rydberg

    @property
    def hyperfine(self):
        self.update_sequence()

        self.__cache__.skip_sequence_build = False
        self.__cache__.waveform = None
        self.__cache__.level_coupling = None
        self.__cache__.field_name = None
        self.__cache__.locations = None
        self.__cache__.scales = None
        self.__cache__.spatial_mod = None
        return super().hyperfine

    @property
    def detuning(self):
        self.update_sequence()

        self.__cache__.skip_sequence_build = False
        self.__cache__.waveform = None
        self.__cache__.field_name = None
        self.__cache__.locations = None
        self.__cache__.scales = None
        self.__cache__.spatial_mod = None
        return super().detuning

    @property
    def rabi(self):
        self.update_sequence()

        self.__cache__.skip_sequence_build = False
        self.__cache__.waveform = None
        self.__cache__.field_name = None
        self.__cache__.locations = None
        self.__cache__.scales = None
        self.__cache__.spatial_mod = None
        return super().rabi

    @property
    def uniform(self):
        self.update_sequence()

        self.__cache__.skip_sequence_build = False
        self.__cache__.waveform = None
        self.__cache__.locations = None
        self.__cache__.scales = None
        self.__cache__.spatial_mod = None
        return super().uniform

    def var(self, name: str):
        self.update_sequence()

        self.__cache__.skip_sequence_build = False
        self.__cache__.waveform = None
        self.__cache__.locations = None
        self.__cache__.scales = None
        self.__cache__.spatial_mod = None
        return super().var(name)

    def location(self, label: int):
        self.update_sequence()

        self.__cache__.skip_sequence_build = False
        self.__cache__.waveform = None
        self.__cache__.locations = None
        self.__cache__.scales = None
        self.__cache__.spatial_mod = None
        return super().location(label)


class TerminateWithWaveform(Terminate):
    def apply(self, waveform: ir.Waveform) -> Route:
        self.__cache__.waveform = waveform
        return Route(self)


class Scale(Location, TerminateWithWaveform):
    def scale(self, scale: ir.Scalar | float | str):
        # __cache__.scales won't be None
        value = ir.cast(scale)
        self.__cache__.scales.pop()
        self.__cache__.scales.append(value)
        return WaveformOrTerminate(self)


class ScaleOrWaveform(Scale, Waveform):
    pass


class WaveformOrTerminate(Waveform, TerminateWithWaveform):
    pass


class Start(LevelCouping, Field, SpatialModulation, Waveform, Terminate):
    def apply(self, seq: ir.Sequence) -> Route:
        self.__cache__.sequence = seq
        self.__cache__.skip_sequence_build = True
        return Route(self)
