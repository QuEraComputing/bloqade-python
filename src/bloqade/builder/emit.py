from bloqade.builder.base import Builder
import bloqade.ir as ir

from bloqade.submission.base import SubmissionBackend
from bloqade.submission.braket import BraketBackend
from bloqade.submission.mock import DumbMockBackend
from bloqade.submission.quera import QuEraBackend
from bloqade.submission.ir.braket import to_braket_task_ir

from bloqade.ir import Program
from bloqade.ir.location.base import AtomArrangement, ParallelRegister

from pydantic import BaseModel
from typing import Optional, Dict, Union, List, Any, Tuple
import numbers
import json
import os
from bloqade.task import HardwareTask, HardwareBatchTask
from bloqade.task.braket_simulator import BraketEmulatorBatchTask, BraketEmulatorTask
from itertools import repeat
from collections import OrderedDict


class BuildError(Exception):
    pass


class BuildState(BaseModel):
    waveform: Optional[ir.Waveform] = None
    waveform_build: Optional[ir.Waveform] = None

    waveform_slice: Optional[Tuple[Optional[ir.Scalar], Optional[ir.Scalar]]] = None
    waveform_record: Optional[str] = None
    spatial_modulation: Optional[ir.SpatialModulation] = None
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

    def __init__(
        self,
        builder: Builder,
        assignments: Dict[str, Union[numbers.Real, List[numbers.Real]]] = {},
        batch: Dict[str, Union[List[numbers.Real], List[List[numbers.Real]]]] = {},
        register: Optional[Union["AtomArrangement", "ParallelRegister"]] = None,
        sequence: Optional[ir.Sequence] = None,
    ) -> None:
        super().__init__(builder)
        self.__batch__ = {}
        if batch:
            first_key, *other_keys = batch.keys()
            first_value = batch[first_key]

            batch_size = len(first_value)
            self.__batch__[first_key] = first_value

            for key in other_keys:
                value = batch[key]
                other_batch_size = len(value)
                if other_batch_size != batch_size:
                    raise ValueError(
                        "mismatch in size of batches, found batch size "
                        f"{batch_size} for {first_key} and a batch size of "
                        f"{other_batch_size} for {key}"
                    )

                self.__batch__[key] = value

        self.__assignments__ = assignments
        self.__sequence__ = sequence
        self.__register__ = register

    def assign(self, **assignments):
        """
        Assign values to variables declared previously in the program.

        Args:
            assignments (Dict[str, Union[Number]]):
            The assignments, which should be a kwargs
            where the key is the variable name and the
            value is the value to assign to the variable.

        Examples:
            - Assign the value 0.0 to the variable "ival"
            and 0.5 to the variable "span_time".

            >>> reg = bloqade.start
            ...       .add_positions([(0,0),(1,1),(2,2),(3,3)])
            >>> seq = reg.rydberg.detuning.uniform
            ...       .linear(start="ival",stop=1,duration="span_time")
            >>> seq = seq.assign(span_time = 0.5, ival = 0.0)

        """

        # these methods terminate no build steps can
        # happens after this other than updating parameters
        new_assignments = dict(self.__assignments__)
        new_assignments.update(**assignments)
        return Emit(
            self,
            assignments=new_assignments,
            batch=self.__batch__,
            register=self.__register__,
            sequence=self.__sequence__,
        )

    def batch_assign(self, **batch):
        """
        Assign values to variables declared previously in the program
        for launching batch jobs.


        Args:
            batch (Dict[str, Union[Number]]): The batch assignments of variables,
            which should be a kwargs where the key is the variable name
            and the value is the list of value assign to the variable.

        Examples:
            - Assign the value [0.0,0.5] to the variable "ival" and [0.6,0.8]
            to the variable "span_time".
            This will create a job with two tasks
            of (value,ival) = (0.0,0.6) and (0.5,0.8) with each has 10 shots.

            >>> reg = bloqade.start.add_positions([(0,0),(1,1),(2,2),(3,3)])
            >>> seq = reg.rydberg.detuning.uniform
            ...       .linear(start="ival",stop=1,duration="span_time")
            >>> job = seq.batch_assign(span_time = [0.6,0.8], ival = [0.0,0.5]).mock(10)

        Note:
            the length of the lists of values should be the same for each variable.

        """

        new_batch = dict(self.__batch__)
        new_batch.update(**batch)
        return Emit(
            self,
            assignments=self.__assignments__,
            batch=new_batch,
            register=self.__register__,
            sequence=self.__sequence__,
        )

    def parallelize(self, cluster_spacing: Any) -> "Emit":
        """
        Parallelize the current problem (register & sequnece) to fill entire FOV
        with the given cluster spacing.

        Args:
            cluster_spacing (Any, should be Real):
            the spacing between parallel clusters.

        Examples:
            - Parallelize the current problem with cluster spacing 7.2 um.

            >>> prob = (
                    bloqade.start.add_positions([(0,0),(1,1),(2,2),(3,3)])
                    .rydberg.detuning.uniform
                    .linear(start=0,stop=1,duration=1)
                    )
            >>> prob = prob.parallelize(7.2)

        """

        if isinstance(self.register, ParallelRegister):
            raise TypeError("cannot parallelize a parallel register.")

        parallel_register = ParallelRegister(self.register, cluster_spacing)
        return Emit(
            self,
            assignments=self.__assignments__,
            batch=self.__batch__,
            register=parallel_register,
            sequence=self.__sequence__,
        )

    @staticmethod
    def __terminate_waveform_append(build_state):
        # this function denotes the termination
        # of a sequence of dots that are appending
        # one waveform to another. This is necessary
        # because the builder traverses the tree in the
        # opposite order of the waveform AST
        # hence we need to have a way to terminate the
        # append sequence and apply the wrapper nodes.
        # These particular nodes wrap the sequence of appended
        # waveforms and then reset the append sequence
        # in the future we can add to this list of nodes.
        if build_state.waveform_build is None:
            return

        if build_state.waveform_slice:
            start_value, stop_value = build_state.waveform_slice
            build_state.waveform_build = build_state.waveform_build[
                start_value:stop_value
            ]
            build_state.waveform_slice = None

        if build_state.waveform_record:
            build_state.waveform_build = build_state.waveform_build.record(
                build_state.waveform_record
            )
            build_state.waveform_record = None

        if build_state.waveform:
            build_state.waveform = build_state.waveform_build.append(
                build_state.waveform
            )
        else:
            build_state.waveform = build_state.waveform_build

        build_state.waveform_build = None

    @staticmethod
    def __terminate_spatial_modulation(build_state: BuildState):
        Emit.__terminate_waveform_append(build_state)
        if build_state.spatial_modulation in build_state.field.value:
            build_state.field.value[
                build_state.spatial_modulation
            ] = build_state.field.value[build_state.spatial_modulation].append(
                build_state.waveform
            )
        else:
            build_state.field.value[
                build_state.spatial_modulation
            ] = build_state.waveform

        build_state.waveform = None

    @staticmethod
    def __build_ast(builder: Builder, build_state: BuildState):
        import bloqade.builder.waveform as waveform
        import bloqade.builder.location as location
        import bloqade.builder.spatial as spatial
        import bloqade.builder.field as field
        import bloqade.builder.coupling as coupling
        import bloqade.builder.start as start

        # print(type(build_state.waveform))
        match builder:
            case (
                waveform.Linear()
                | waveform.Poly()
                | waveform.Constant()
                | waveform.Apply()
                | waveform.PythonFn()
            ):
                # because builder traverese the tree in the opposite order
                # the builder must be appended to the current waveform.
                if build_state.waveform_build:
                    build_state.waveform_build = builder._waveform.append(
                        build_state.waveform_build
                    )
                else:
                    build_state.waveform_build = builder._waveform
                Emit.__build_ast(builder.__parent__, build_state)

            case location.Scale() if isinstance(
                builder.__parent__.__parent__, spatial.SpatialModulation
            ):
                Emit.__terminate_waveform_append(build_state)

                scale = builder._scale
                loc = ir.Location(builder.__parent__._label)
                build_state.scaled_locations.value[loc] = scale
                build_state.spatial_modulation = build_state.scaled_locations
                build_state.scaled_locations = ir.ScaledLocations({})
                Emit.__terminate_spatial_modulation(build_state)

                Emit.__build_ast(builder.__parent__.__parent__, build_state)

            case waveform.Sample():
                if build_state.waveform_build:
                    build_state.waveform_build = ir.Sample(
                        builder.__parent__._waveform,
                        dt=builder._dt,
                        interpolation=builder._interpolation,
                    ).append(build_state.waveform_build)

                else:
                    build_state.waveform_build = ir.Sample(
                        builder.__parent__._waveform,
                        dt=builder._dt,
                        interpolation=builder._interpolation,
                    )
                Emit.__build_ast(builder.__parent__.__parent__, build_state)

            case waveform.Record() if isinstance(builder.__parent__, waveform.Slice):
                Emit.__terminate_waveform_append(build_state)

                build_state.waveform_slice = (
                    builder.__parent__._start,
                    builder.__parent__._stop,
                )
                build_state.waveform_record = builder._name

                Emit.__build_ast(builder.__parent__.__parent__, build_state)

            case waveform.Slice():
                Emit.__terminate_waveform_append(build_state)
                build_state.waveform_slice = (builder._start, builder._stop)
                Emit.__build_ast(builder.__parent__, build_state)

            case waveform.Record():
                Emit.__terminate_waveform_append(build_state)
                build_state.waveform_record = builder._name
                Emit.__build_ast(builder.__parent__, build_state)

            case location.Location() if isinstance(
                builder.__parent__, spatial.SpatialModulation
            ):
                Emit.__terminate_waveform_append(build_state)
                scale = ir.cast(1.0)
                loc = ir.Location(builder._label)
                # update current list of scaled locations
                build_state.scaled_locations.value[loc] = scale
                # copy scaled locations to the current spatial modulation
                build_state.spatial_modulation = build_state.scaled_locations
                # reset scaled locations
                build_state.scaled_locations = ir.ScaledLocations({})
                # terminate building of a field
                Emit.__terminate_spatial_modulation(build_state)

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
                print("here")
                build_state.spatial_modulation = ir.Uniform
                Emit.__terminate_spatial_modulation(build_state)
                Emit.__build_ast(builder.__parent__, build_state)

            case location.Var():
                build_state.spatial_modulation = ir.RunTimeVector(builder._name)
                Emit.__terminate_spatial_modulation(build_state)
                Emit.__build_ast(builder.__parent__, build_state)

            case field.Detuning():
                build_state.detuning = build_state.detuning.add(build_state.field)
                # reset build_state values
                build_state.field = ir.Field({})
                Emit.__build_ast(builder.__parent__, build_state)

            case field.Rabi():
                Emit.__build_ast(builder.__parent__, build_state)

            case field.Amplitude():
                build_state.amplitude = build_state.amplitude.add(build_state.field)

                # reset build_state values
                build_state.field = ir.Field({})
                Emit.__build_ast(builder.__parent__, build_state)

            case field.Phase():
                build_state.phase = build_state.phase.add(build_state.field)

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

            case Emit():
                Emit.__build_ast(builder.__parent__, build_state)

            case _:
                raise RuntimeError(f"invalid builder type: {builder.__class__}")

    def __assignments_iterator(self):
        assignments = dict(self.__assignments__)

        if self.__batch__:
            batch_iterators = [
                zip(repeat(name), values) for name, values in self.__batch__.items()
            ]
            batch_iterator = zip(*batch_iterators)

            for batch_list in batch_iterator:
                assignments.update(dict(batch_list))
                yield assignments
        else:
            yield assignments

    def __compile_hardware(
        self, nshots: int, backend: SubmissionBackend
    ) -> HardwareBatchTask:
        from bloqade.codegen.hardware.quera import SchemaCodeGen

        capabilities = backend.get_capabilities()
        tasks = OrderedDict()

        for task_number, assignments in enumerate(self.__assignments_iterator()):
            schema_compiler = SchemaCodeGen(assignments, capabilities=capabilities)
            task_ir = schema_compiler.emit(nshots, self.program)
            task_ir = task_ir.discretize(capabilities)
            tasks[task_number] = HardwareTask(
                task_ir=task_ir,
                backend=backend,
                parallel_decoder=schema_compiler.parallel_decoder,
            )

        return HardwareBatchTask(hardware_tasks=tasks)

    @property
    def register(self) -> Union["AtomArrangement", "ParallelRegister"]:
        """Get the `register` from the current builder.

        Returns:
            register (Union["AtomArrangement", "ParallelRegister"])

        Note:
            If the program is built with
            [`parallelize()`][bloqade.builder.emit.Emit.parallelize],
            The the register will be a
            [`ParallelRegister`][bloqade.ir.location.base.ParallelRegister].
            Otherwise it will be a
            [`AtomArrangement`][bloqade.ir.location.base.AtomArrangement].

        """
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
        """Get the `sequence` from the current builder.

        Returns:
            sequence (Sequence)

        """
        if self.__sequence__ is None:
            build_state = BuildState()
            Emit.__build_ast(self, build_state)
            self.__sequence__ = build_state.sequence

        return self.__sequence__

    @property
    def program(self) -> Program:
        """
        Get the Program from the current builder.
        See also [`Program`][bloqade.ir.program.Program]

        Returns:
            prog (Program)

        """
        return Program(self.register, self.sequence)

    def simu(self, *args, **kwargs):
        raise NotImplementedError

    def braket_local_simulator(self, nshots: int):
        """
        Compile the current builder to a
        [`BraketEmulatorBatchTask`][bloqade.task.braket_simulator.BraketEmulatorBatchTask]
        , which can be submit to run on braket local simulator.

        Args:
            nshots (int): The number of shots to run.

        Returns:
            BraketEmulatorJob

        """
        from bloqade.codegen.hardware.quera import SchemaCodeGen

        if isinstance(self.register, ParallelRegister):
            raise TypeError("Braket emulator doesn't support parallel registers.")

        tasks = OrderedDict()

        for task_number, assignments in enumerate(self.__assignments_iterator()):
            schema_compiler = SchemaCodeGen(assignments)
            task_ir = schema_compiler.emit(nshots, self.program)
            task = BraketEmulatorTask(task_ir=to_braket_task_ir(task_ir))
            tasks[task_number] = task

        return BraketEmulatorBatchTask(braket_emulator_tasks=tasks)

    def braket(self, nshots: int) -> "HardwareBatchTask":
        """
        Compile the current builder to a Amazon braket
        [`HardwareBatchTask`][bloqade.task.hardware.HardwareBatchTask]
        , which can be submit to run on QPU through braket service.

        Args:
            nshots (int): The number of shots to run.

        Returns:
            HardwareBatchTask

        """
        backend = BraketBackend()
        return self.__compile_hardware(nshots, backend)

    def quera(
        self, nshots: int, config_file: Optional[str] = None, **api_config
    ) -> "HardwareBatchTask":
        """
        Compile the current builder to a QuEra
        [`HardwareBatchTask`][bloqade.task.hardware.HardwareBatchTask]
        , which can be submit to run on QPU through QuEra service.

        Args:
            nshots (int): The number of shots to run.
            config_file (Optional[str]): The path to the config file.
            api_config (Dict[str, Any]): The api config.

        Returns:
            HardwareBatchTask

        """
        if config_file is None:
            path = os.path.dirname(__file__)

            config_file = os.path.join(
                path,
                "..",
                "submission",
                "quera_api_client",
                "config",
                "integ_quera_api.json",
            )

        if len(api_config) == 0:
            with open(config_file, "r") as io:
                api_config.update(**json.load(io))

        backend = QuEraBackend(**api_config)

        return self.__compile_hardware(nshots, backend)

    def mock(
        self, nshots: int, state_file: str = ".mock_state.txt"
    ) -> "HardwareBatchTask":
        """
        Compile the current builder to a Dummy mock
        [`HardwareBatchTask`][bloqade.task.hardware.HardwareBatchTask]
        , which can be used for testing.

        Args:
            nshots (int): The number of shots to run.
            state_file (str): The file to store the state of the mock backend.

        Returns:
            HardwareBatchTask

        """
        backend = DumbMockBackend(state_file=state_file)

        return self.__compile_hardware(nshots, backend)
