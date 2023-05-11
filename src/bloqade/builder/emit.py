from bloqade.builder.base import Builder
import bloqade.builder.waveform as waveform
import bloqade.builder.location as location
import bloqade.builder.field as field
import bloqade.builder.coupling as coupling
import bloqade.builder.start as start
import bloqade.ir as ir
from pydantic import BaseModel
from typing import Optional, Dict


class BuildError(Exception):
    pass


class BuildState(BaseModel):
    sequence: Optional[ir.Sequence] = None
    waveform: Optional[ir.Waveform] = None
    spatial_modulation: Optional[ir.SpatialModulation] = None

    scaled_locations: Dict[ir.Location, ir.Scalar] = {}
    detuning: ir.Field = ir.Field({})
    amplitude: ir.Field = ir.Field({})
    phase: ir.Field = ir.Field({})
    rydberg: ir.Pulse = ir.Pulse({})
    hyperfine: ir.Pulse = ir.Pulse({})
    sequence: ir.Sequence = ir.Sequence({})


class Emit(Builder):
    # NOTE: this will mutate the builder
    # because once methods inside this class are called
    # the building process will terminate
    # none of the methods in this class will return a Builder

    def __init__(self, builder: Builder) -> None:
        super().__init__(builder)
        self.__assignments = None
        self.__sequence = None

    def assign(self, **assignments):
        self.__assignments = assignments

    @staticmethod
    def __build(builder: Builder, build_state: BuildState):
        match builder:
            case (
                waveform.Linear()
                | waveform.Poly()
                | waveform.Constant()
                | waveform.Apply()
            ):
                if build_state.waveform:
                    build_state.waveform.append(builder._waveform)
                else:
                    build_state.waveform = builder._waveform
                Emit.__build(builder.__parent__, build_state)

            case location.Scale() if isinstance(builder.__parent__, location.Location):
                parent = builder.__parent__
                scale = builder._scale
                loc = ir.Location(parent._label)
                if build_state.spatial_modulation is None:
                    build_state.spatial_modulation = ir.ScaledLocations({loc: scale})
                else:
                    build_state.spatial_modulation.value[loc] = scale
                Emit.__build(parent.__parent__, build_state)

            case location.Location():
                scale = ir.cast(1.0)
                loc = ir.Location(builder._label)
                if build_state.spatial_modulation is None:
                    build_state.spatial_modulation = ir.ScaledLocations({loc: scale})
                else:
                    build_state.spatial_modulation.value[loc] = scale
                Emit.__build(builder.__parent__, build_state)

            case location.Uniform():
                build_state.spatial_modulation = ir.Uniform
                Emit.__build(builder.__parent__, build_state)

            case location.Var():
                build_state.spatial_modulation = ir.RunTimeVector(builder._name)
                Emit.__build(builder.__parent__, build_state)

            case field.Detuning():
                build_state.detuning = build_state.detuning.add(
                    ir.Field({build_state.spatial_modulation: build_state.waveform})
                )

                # reset build_state values
                build_state.waveform = None
                build_state.spatial_modulation = None
                Emit.__build(builder.__parent__, build_state)

            case field.Amplitude():
                build_state.amplitude = build_state.amplitude.add(
                    ir.Field({build_state.spatial_modulation: build_state.waveform})
                )

                # reset build_state values
                build_state.waveform = None
                build_state.spatial_modulation = None
                Emit.__build(builder.__parent__, build_state)

            case field.Phase():
                build_state.phase = build_state.phase.add(
                    ir.Field({build_state.spatial_modulation: build_state.waveform})
                )

                # reset build_state values
                build_state.waveform = None
                build_state.spatial_modulation = None
                Emit.__build(builder.__parent__, build_state)

            case coupling.Rydberg():
                if build_state.amplitude:
                    current_field = build_state.rydberg.value.get(
                        ir.rabi.amplitude, ir.Field({})
                    )
                    result_field = current_field.add(build_state.amplitude)
                    build_state.rydberg.value[ir.rabi.amplitude] = result_field

                if build_state.phase:
                    current_field = build_state.rydberg.value.get(
                        ir.rabi.phase, ir.Field({})
                    )
                    result_field = current_field.add(build_state.phase)
                    build_state.rydberg.value[ir.rabi.phase] = result_field

                if build_state.detuning:
                    current_field = build_state.rydberg.value.get(
                        ir.detuning, ir.Field({})
                    )
                    result_field = current_field.add(build_state.detuning)
                    build_state.rydberg.value[ir.detuning] = result_field

                # reset fields
                build_state.amplitude = ir.Field({})
                build_state.phase = ir.Field({})
                build_state.detuning = ir.Field({})
                Emit.__build(builder.__parent__, build_state)

            case coupling.Hyperfine():
                if build_state.amplitude:
                    current_field = build_state.hyperfine.value.get(
                        ir.rabi.amplitude, ir.Field({})
                    )
                    result_field = current_field.add(build_state.amplitude)
                    build_state.hyperfine.value[ir.rabi.amplitude] = result_field

                if build_state.phase:
                    current_field = build_state.hyperfine.value.get(
                        ir.rabi.phase, ir.Field({})
                    )
                    result_field = current_field.add(build_state.phase)
                    build_state.hyperfine.value[ir.rabi.phase] = result_field

                if build_state.detuning:
                    current_field = build_state.hyperfine.value.get(
                        ir.detuning, ir.Field({})
                    )
                    result_field = current_field.add(build_state.detuning)
                    build_state.hyperfine.value[ir.detuning] = result_field

                Emit.__build(builder.__parent__, build_state)

            case start.ProgramStart():
                if build_state.rydberg:
                    build_state.sequence.value[ir.rydberg] = build_state.rydber

                if build_state.hyperfine:
                    build_state.sequence.value[ir.hyperfine] = build_state.hyperfine

                build_state.rydberg = ir.Pulse({})
                build_state.hyperfine = ir.Pulse({})

            case _:
                raise RuntimeError(f"invalid builder type: {builder.__class__}")

    @property
    def sequence(self):
        build_state = BuildState()
        if self.__sequence is None:
            Emit.__build(self, build_state)

            self.__sequence = build_state.sequence

        return self.__sequence

    def quera(self):  # -> return QuEraSchema object
        pass

    def braket(self):  # -> return BraketSchema object
        pass

    def simu(self):  # -> Simulation object
        pass
