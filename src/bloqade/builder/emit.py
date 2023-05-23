from bloqade.builder.base import Builder
import bloqade.builder.waveform as waveform
import bloqade.builder.location as location
import bloqade.builder.spatial as spatial
import bloqade.builder.field as field
import bloqade.builder.coupling as coupling
import bloqade.builder.start as start
import bloqade.ir as ir

from bloqade.submission.base import SubmissionBackend
from bloqade.submission.braket import BraketBackend
from bloqade.submission.mock import DumbMockBackend
from bloqade.submission.quera import QuEraBackend
from bloqade.submission.ir.braket import to_braket_task_ir

from bloqade.ir import Program

from pydantic import BaseModel
from typing import Optional
import json
import os
from bloqade.task import HardwareTask, HardwareJob


class BuildError(Exception):
    pass


class BuildState(BaseModel):
    waveform: Optional[ir.Waveform] = None
    scaled_locations: ir.ScaledLocations = ir.ScaledLocations({})
    field: ir.Field = ir.Field({})
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
        self.__assignments__ = {}
        self.__sequence__ = None
        self.__register__ = None

    def assign(self, **assignments):
        self.__assignments__.update(assignments)
        return self

    @staticmethod
    def __build_ast(builder: Builder, build_state: BuildState):
        match builder:
            case (
                waveform.Linear()
                | waveform.Poly()
                | waveform.Constant()
                | waveform.Apply()
            ):
                # because builder traverese the tree in the opposite order
                # the builder must be appended to the current waveform.
                if build_state.waveform:
                    build_state.waveform = builder._waveform.append(
                        build_state.waveform
                    )
                else:
                    build_state.waveform = builder._waveform
                Emit.__build_ast(builder.__parent__, build_state)

            case location.Scale() if isinstance(
                builder.__parent__.__parent__, spatial.SpatialModulation
            ):
                scale = builder._scale
                loc = ir.Location(builder.__parent__._label)
                build_state.scaled_locations.value[loc] = scale

                new_field = ir.Field(
                    {build_state.scaled_locations: build_state.waveform}
                )
                build_state.field = build_state.field.add(new_field)

                build_state.scaled_locations = ir.ScaledLocations({})
                build_state.waveform = None

                Emit.__build_ast(builder.__parent__.__parent__, build_state)

            case location.Location() if isinstance(
                builder.__parent__, spatial.SpatialModulation
            ):
                scale = ir.cast(1.0)
                loc = ir.Location(builder._label)
                build_state.scaled_locations.value[loc] = scale

                new_field = ir.Field(
                    {build_state.scaled_locations: build_state.waveform}
                )
                build_state.field = build_state.field.add(new_field)

                build_state.scaled_locations = ir.ScaledLocations({})
                build_state.waveform = None

                Emit.__build_ast(builder.__parent__, build_state)

            case location.Scale():
                scale = builder._scale
                loc = ir.Location(builder.__parent__._label)
                build_state.scaled_locations.value[loc] = scale

                Emit.__build_ast(builder.__parent__.__parent__, build_state)

            case location.Location():
                scale = ir.cast(1.0)
                loc = ir.Location(builder._label)
                build_state.scaled_locations.value[loc] = scale

                Emit.__build_ast(builder.__parent__, build_state)

            case location.Uniform():
                new_field = ir.Field({ir.Uniform: build_state.waveform})
                build_state.field = build_state.field.add(new_field)

                # reset build_state values
                build_state.waveform = None
                Emit.__build_ast(builder.__parent__, build_state)

            case location.Var():
                new_field = ir.Field(
                    {ir.RunTimeVector(builder._name): build_state.waveform}
                )
                build_state.field = build_state.field.add(new_field)

                # reset build_state values
                build_state.waveform = None
                Emit.__build_ast(builder.__parent__, build_state)

            case field.Detuning():
                build_state.detuning = build_state.detuning.add(build_state.field)

                # reset build_state values
                build_state.field = ir.Field({})
                Emit.__build_ast(builder.__parent__, build_state)

            case field.Rabi():
                Emit.__build_ast(builder.__parent__, build_state)

            case field.Amplitude():
                build_state.amplitude = build_state.detuning.add(build_state.field)

                # reset build_state values
                build_state.field = ir.Field({})
                Emit.__build_ast(builder.__parent__, build_state)

            case field.Phase():
                build_state.phase = build_state.detuning.add(build_state.field)

                # reset build_state values
                build_state.field = ir.Field({})
                Emit.__build_ast(builder.__parent__, build_state)

            case coupling.Rydberg():
                if build_state.amplitude.value:
                    current_field = build_state.rydberg.value.get(
                        ir.rabi.amplitude, ir.Field({})
                    )
                    result_field = current_field.add(build_state.amplitude)
                    build_state.rydberg.value[ir.rabi.amplitude] = result_field

                if build_state.phase.value:
                    current_field = build_state.rydberg.value.get(
                        ir.rabi.phase, ir.Field({})
                    )
                    result_field = current_field.add(build_state.phase)
                    build_state.rydberg.value[ir.rabi.phase] = result_field

                if build_state.detuning.value:
                    current_field = build_state.rydberg.value.get(
                        ir.detuning, ir.Field({})
                    )
                    result_field = current_field.add(build_state.detuning)
                    build_state.rydberg.value[ir.detuning] = result_field

                # reset fields
                build_state.amplitude = ir.Field({})
                build_state.phase = ir.Field({})
                build_state.detuning = ir.Field({})
                Emit.__build_ast(builder.__parent__, build_state)

            case coupling.Hyperfine():
                if build_state.amplitude.value:
                    current_field = build_state.hyperfine.value.get(
                        ir.rabi.amplitude, ir.Field({})
                    )
                    result_field = current_field.add(build_state.amplitude)
                    build_state.hyperfine.value[ir.rabi.amplitude] = result_field

                if build_state.phase.value:
                    current_field = build_state.hyperfine.value.get(
                        ir.rabi.phase, ir.Field({})
                    )
                    result_field = current_field.add(build_state.phase)
                    build_state.hyperfine.value[ir.rabi.phase] = result_field

                if build_state.detuning.value:
                    current_field = build_state.hyperfine.value.get(
                        ir.detuning, ir.Field({})
                    )
                    result_field = current_field.add(build_state.detuning)
                    build_state.hyperfine.value[ir.detuning] = result_field

                Emit.__build_ast(builder.__parent__, build_state)

            case start.ProgramStart():
                if build_state.rydberg.value:
                    build_state.sequence.value[ir.rydberg] = build_state.rydberg

                if build_state.hyperfine.value:
                    build_state.sequence.value[ir.hyperfine] = build_state.hyperfine

                build_state.rydberg = ir.Pulse({})
                build_state.hyperfine = ir.Pulse({})

            case _:
                raise RuntimeError(f"invalid builder type: {builder.__class__}")

    @property
    def register(self):
        if self.__register__:
            return self.__register__

        current = self
        while current.__parent__ is not None:
            if current.__register__ is not None:
                self.__register__ = current.__register__
                return self.__register__

            current = current.__parent__

        self.__register__ = current.__register__

        if self.__register__ is None:
            raise AttributeError("No reigster found in builder.")

        return self.__register__

    @property
    def sequence(self):
        if self.__sequence__ is None:
            build_state = BuildState()
            Emit.__build_ast(self, build_state)
            self.__sequence__ = build_state.sequence

        return self.__sequence__

    @property
    def program(self) -> Program:
        return Program(self.register, self.sequence)

    def __compile_task_ir(self, nshots: int, backend: SubmissionBackend):
        from bloqade.codegen.quera_hardware import SchemaCodeGen

        capabilities = backend.get_capabilities()
        schema_compiler = SchemaCodeGen(self.__assignments__, capabilities)
        task_ir = schema_compiler.emit(nshots, self.program)
        task_ir = task_ir.discretize(capabilities)

        if isinstance(backend, BraketBackend):
            task_ir = to_braket_task_ir(task_ir)

        return (task_ir, schema_compiler.multiplex_decoder)

    def simu(self, *args, **kwargs):
        raise NotImplementedError

    def braket(self, nshots: int) -> "HardwareJob":
        backend = BraketBackend()
        task_ir, multiplex_decoder = self.__compile_task_ir(nshots, backend)

        hardware_task = HardwareTask(braket_task_ir=task_ir, braket_backend=backend)

        return HardwareJob(tasks=[hardware_task], multiplex_decoder=multiplex_decoder)

    def quera(self, nshots: int, config_file: Optional[str] = None) -> "HardwareTask":
        if config_file is None:
            path = os.path.dirname(__file__)
            api_config_file = os.path.join(
                path, "submission", "quera_api_client", "config", "dev_quera_api.json"
            )
            with open(api_config_file, "r") as io:
                api_config = json.load(io)

            backend = QuEraBackend(**api_config)

        task_ir, multiplex_decoder = self.__compile_task_ir(nshots, backend)
        hardware_task = HardwareTask(quera_task_ir=task_ir, quera_backend=backend)

        return HardwareJob(tasks=[hardware_task], multiplex_decoder=multiplex_decoder)

    def mock(self, nshots: int, state_file: str = ".mock_state.txt") -> "HardwareJob":
        backend = DumbMockBackend(state_file=state_file)
        task_ir, multiplex_decoder = self.__compile_task_ir(nshots, backend)

        hardware_task = HardwareTask(quera_task_ir=task_ir, mock_backend=backend)

        return HardwareJob(tasks=[hardware_task], multiplex_decoder=multiplex_decoder)
