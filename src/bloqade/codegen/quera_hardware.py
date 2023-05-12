from bloqade.ir.scalar import Literal
import bloqade.ir.waveform as waveform
from bloqade.ir.field import (
    Field,
    Location,
    SpatialModulation,
    ScaledLocations,
    RunTimeVector,
    Uniform,
)
from bloqade.ir.pulse import (
    PulseExpr,
    Pulse,
    NamedPulse,
    RabiFrequencyAmplitude,
    RabiFrequencyPhase,
    Detuning,
)
from bloqade.ir.sequence import (
    SequenceExpr,
    Sequence,
    NamedSequence,
    RydbergLevelCoupling,
    HyperfineLevelCoupling,
)
from bloqade.codegen.program_visitor import ProgramVisitor
from bloqade.codegen.waveform_visitor import WaveformVisitor
from bloqade.codegen.assignment_scan import AssignmentScan

import quera_ahs_utils.quera_ir.task_specification as task_spec
from typing import Dict, Tuple, List, TYPE_CHECKING
from bisect import bisect_left

from bloqade.lattice.multiplex_decoder import MultiplexDecoder

if TYPE_CHECKING:
    from bloqade.lattice.base import Lattice
    from bloqade.task import Program


class PiecewiseLinearCodeGen(WaveformVisitor):
    def __init__(self, assignments: Dict[str, float]):
        self.assignments = assignments

    def visit_negative(self, ast: waveform.Negative) -> Tuple[List[float], List[float]]:
        times, values = ast.waveform
        return times, [-value for value in values]

    def visit_scale(self, ast: waveform.Scale) -> Tuple[List[float], List[float]]:
        times, values = self.visit(ast.waveform)
        scaler = ast.scalar(**self.assignments)
        return times, [scaler * value for value in values]

    def visit_linear(self, ast: waveform.Linear) -> Tuple[List[float], List[float]]:
        duration = ast.duration(**self.assignments)
        start = ast.start(**self.assignments)
        stop = ast.stop(**self.assignments)

        return [0, duration], [start, stop]

    def visit_constant(self, ast: waveform.Constant) -> Tuple[List[float], List[float]]:
        duration = ast.duration(**self.assignments)
        value = ast.value(**self.assignments)

        return [0, duration], [value, value]

    def visit_poly(self, ast: waveform.Poly) -> Tuple[List[float], List[float]]:
        match ast:
            case waveform.Poly(
                checkpoints=checkpoint_exprs, duration=duration_expr
            ) if len(checkpoint_exprs) == 1:
                duration = duration_expr(**self.assignments)
                (value,) = [
                    checkpoint_expr(**self.assignments)
                    for checkpoint_expr in checkpoint_exprs
                ]
                return [0, duration], [value, value]

            case waveform.Poly(
                checkpoints=checkpoint_exprs, duration=duration_expr
            ) if len(checkpoint_exprs) == 2:
                duration = duration_expr(**self.assignments)
                values = [
                    checkpoint_expr(**self.assignments)
                    for checkpoint_expr in checkpoint_exprs
                ]

                start = values[0]
                stop = values[0] + values[1] * duration

                return [0, duration], [start, stop]

            case waveform.Poly(checkpoints=checkpoints):
                order = len(checkpoints) - 1
                raise ValueError(
                    "Failed to compile Waveform to piecewise linear,"
                    f"found Polynomial of order {order}."
                )

    def visit_slice(self, ast: waveform.Slice) -> Tuple[List[float], List[float]]:
        duration = ast.waveform.duration(**self.assignments)

        start_time = ast.iterval.start(**self.assignments)
        stop_time = ast.interval.stop(**self.assignments)

        if start_time < 0:
            raise ValueError((f"start time for slice {start_time} is smaller than 0."))

        if stop_time > duration:
            raise ValueError(
                (f"end time for slice {stop_time} is larger than duration {duration}.")
            )

        if stop_time < start_time:
            raise ValueError(
                (
                    f"end time for slice {stop_time} is smaller than "
                    f"starting value for slice {start_time}."
                )
            )

        start_value = ast.waveform(start_time, **self.assignments)
        stop_value = ast.waveform(stop_time, **self.assignments)

        times, values = self.visit(ast.waveform)

        start_index = bisect_left(times, start_time)
        stop_index = bisect_left(times, stop_time)

        absolute_times = [start_time] + times[start_index:stop_index] + [stop_time]

        times = [time - start_time for time in absolute_times]
        values = [start_value] + values[start_index:stop_index] + [stop_value]

        return times, values

    def visit_append(self, ast: waveform.Append) -> Tuple[List[float], List[float]]:
        times, values = self.visit(ast.waveforms[0])

        for sub_expr in ast.waveforms[1:]:
            new_times, new_values = self.visit(sub_expr)

            if values[-1] != new_values[0]:
                diff = abs(new_values[0] - values[-1])
                raise ValueError(
                    f"discontinuity with a jump of {diff} found when compiling to "
                    "piecewise linear."
                )

            shifted_times = [time + times[-1] for time in new_times[1:]]
            times.extend(shifted_times)
            values.extend(new_values[1:])

        return times, values


class PiecewiseConstantCodeGen(WaveformVisitor):
    def __init__(self, assignments: Dict[str, float]):
        self.assignments = assignments

    def visit_negative(self, ast: waveform.Negative) -> Tuple[List[float], List[float]]:
        times, values = ast.waveform
        return times, [-value for value in values]

    def visit_scale(self, ast: waveform.Scale) -> Tuple[List[float], List[float]]:
        times, values = self.visit(ast.waveform)
        scaler = ast.scalar(**self.assignments)
        return times, [scaler * value for value in values]

    def visit_linear(self, ast: waveform.Linear) -> Tuple[List[float], List[float]]:
        duration = ast.duration(**self.assignments)
        start = ast.start(**self.assignments)
        stop = ast.stop(**self.assignments)

        if start != stop:
            raise ValueError(
                "Failed to compile Waveform to piecewise constant, "
                "found non-constant Linear piecce."
            )

        return [0, duration], [start, stop]

    def visit_constant(self, ast: waveform.Constant) -> Tuple[List[float], List[float]]:
        duration = ast.duration(**self.assignments)
        value = ast.value(**self.assignments)

        return [0, duration], [value, value]

    def visit_poly(self, ast: waveform.Poly) -> Tuple[List[float], List[float]]:
        match ast:
            case waveform.Poly(
                checkpoints=checkpoint_exprs, duration=duration_expr
            ) if len(checkpoint_exprs) == 1:
                duration = duration_expr(**self.assignments)
                (value,) = [
                    checkpoint_expr(**self.assignments)
                    for checkpoint_expr in checkpoint_exprs
                ]
                return [0, duration], [value, value]

            case waveform.Poly(checkpoints=checkpoints):
                order = len(checkpoints) - 1
                raise ValueError(
                    "Failed to compile Waveform to piecewise constant, "
                    f"found Polynomial of order {order}."
                )

    def visit_slice(self, ast: waveform.Slice) -> Tuple[List[float], List[float]]:
        duration = ast.waveform.duration(**self.assignments)

        start_time = ast.iterval.start(**self.assignments)
        stop_time = ast.interval.stop(**self.assignments)

        if start_time < 0:
            raise ValueError((f"start time for slice {start_time} is smaller than 0."))

        if stop_time > duration:
            raise ValueError(
                (f"end time for slice {stop_time} is larger than duration {duration}.")
            )

        if stop_time < start_time:
            raise ValueError(
                (
                    f"end time for slice {stop_time} is smaller than "
                    f"starting value for slice {start_time}."
                )
            )

        start_value = ast.waveform(start_time, **self.assignments)
        stop_value = ast.waveform(stop_time, **self.assignments)

        times, values = self.visit(ast.waveform)

        start_index = bisect_left(times, start_time)
        stop_index = bisect_left(times, stop_time)

        absolute_times = [start_time] + times[start_index:stop_index] + [stop_time]

        times = [time - start_time for time in absolute_times]
        values = [start_value] + values[start_index:stop_index] + [stop_value]

        return times, values

    def visit_append(self, ast: waveform.Append) -> Tuple[List[float], List[float]]:
        times, values = self.visit(ast.waveforms[0])

        for sub_expr in ast.waveforms[1:]:
            new_times, new_values = self.visit(sub_expr)

            shifted_times = [time + times[-1] for time in new_times[1:]]
            times.extend(shifted_times)
            values[-1] = new_values[0]
            values.extend(new_values[1:])

        return times, values


class SchemaCodeGen(ProgramVisitor):
    def __init__(self):
        self.assignments = None
        self.n_atoms = None
        self.lattice = None
        self.effective_hamiltonian = None
        self.rydberg = None
        self.field_name = None
        self.rabi_frequency_amplitude = None
        self.rabi_frequency_phase = None
        self.detuning = None
        self.lattice_site_coefficients = None

        self.multiplex_mapping = None

    def visit_spatial_modulation(self, ast: SpatialModulation):
        match (self.multiplex_mapping, ast):
            case (None, ScaledLocations(locations)):
                # check that all indices map to actual atoms in lattice
                self.lattice_site_coefficients = []
                for location in locations.keys():
                    if location.value >= self.n_atoms:
                        raise ValueError(
                            f"Location({location.value}) is larger than the lattice."
                        )

                for atom_index in range(self.n_atoms):
                    scale = locations.get(Location(atom_index), Literal(0.0))
                    self.lattice_site_coefficients.append(
                        scale(**self.assignments)
                    )  # append scalars to lattice_site_coefficients

            case (multiplex_mapping, ScaledLocations(locations)):
                self.lattice_site_coefficients = []

                for location in locations.keys():
                    if location.value >= self.n_atoms:
                        raise ValueError(
                            f"Location({location.value}) is larger than the lattice."
                        )

                site_to_cluster_map = MultiplexDecoder(
                    mapping=multiplex_mapping
                ).get_site_indices()

                for atom_index in range(self.n_atoms):
                    scale = locations.get(
                        Location(site_to_cluster_map[atom_index]), Literal(0.0)
                    )
                    self.lattice_site_coefficients.append(scale(**self.assignments))

            case (None, RunTimeVector(name)):
                if len(self.assignments[name]) != self.n_atoms:
                    raise ValueError(
                        f"Coefficient list {name} doesn't match the size of lattice "
                        f"{self.n_atoms}."
                    )

            case (multiplex_mapping, RunTimeVector(name)):
                if len(self.assignments[name]) != self.n_atoms:
                    raise ValueError(
                        f"Coefficient list {name} doesn't match the size of lattice "
                        f"{self.n_atoms}."
                    )

                multiplexed_runtime_vector = []
                for _ in range(self.multiplex_mapping.keys()):
                    multiplexed_runtime_vector += self.assignments[name]

                self.assignments[name] = multiplexed_runtime_vector

    """
    def visit_spatial_modulation(self, ast: SpatialModulation):
        # can use the multiplex mapping and multiplexed enabled features here
        match ast:
            case ScaledLocations(locations): # with and without multiplexing
                self.lattice_site_coefficients = []

                # check that all indices map to actual atoms in lattice
                for location in locations.keys():
                    if location.value >= self.n_atoms:
                        raise ValueError(
                            f"Location({location.value}) is larger than the lattice."
                        )

                # need to get the number of atoms in a single cluster
                # try to use mapping more explicitly
                # use get_site_indices
                # n_atoms_single_cluster = len(list(self.mapping.values())[0])
                site_to_cluster_map = MultiplexDecoder(
                    mapping=self.multiplex_mapping
                ).get_site_indices()

                for atom_index in range(self.n_atoms):
                    # can apply Phillip's modulo operation here
                    if self.multiplex_mapping is not None:
                        scale = locations.get(
                            Location(site_to_cluster_map[atom_index]), Literal(0.0)
                        )
                    else:
                        scale = locations.get(
                            Location(atom_index), Literal(0.0)
                        )  # for each global_site_index,
                        # get the associated scalar,
                        # otherwise default to Literal of (0.0)
                    self.lattice_site_coefficients.append(
                        scale(**self.assignments)
                    )  # append scalars to lattice_site_coefficients

            case RunTimeVector(name): # with and without multiplexing
                run_time_vector = self.assignments[name]
                if len(run_time_vector) != self.n_atoms:
                    raise ValueError(
                        f"Coefficient list {name} doesn't match the size of lattice "
                        f"{self.n_atoms}."
                    )

                # overwrite the existing RunTimeVector with a new one
                if self.multiplex_mapping is not None:
                    # get number of keys in mapping for clusters
                    multiplexed_run_time_vector = []
                    for _ in range(self.multiplex_mapping.keys()):
                        multiplexed_run_time_vector += run_time_vector

                    self.assignments[name] = multiplexed_run_time_vector

            case _:
                raise RuntimeError(
                    "This Error should not appear, please Open up an issue."
                )
"""

    def visit_field(self, ast: Field):
        match (self.field_name, ast):  # Pulse: Dict of FieldName/Field
            # Can only have a global RabiFrequencyAmplitude
            case (RabiFrequencyAmplitude(), Field(terms)) if len(
                terms
            ) == 1 and Uniform in terms:
                times, values = PiecewiseLinearCodeGen(self.assignments).visit(
                    terms[Uniform]
                )

                self.rabi_frequency_amplitude = task_spec.RabiFrequencyAmplitude(
                    global_=task_spec.GlobalField(times=times, values=values)
                )
            # Can only have global RabiFrequencyPhase
            case (RabiFrequencyPhase(), Field(terms)) if len(
                terms
            ) == 1 and Uniform in terms:  # has to be global
                times, values = PiecewiseConstantCodeGen(self.assignments).visit(
                    terms[Uniform]
                )

                self.rabi_frequency_phase = task_spec.RabiFrequencyAmplitude(
                    global_=task_spec.GlobalField(times=times, values=values)
                )

            # 3 possible detuning cases:
            # (global, no local),
            # (local, no global),
            # (local, global)

            ## global detuning, no local
            case (Detuning(), Field(terms)) if len(terms) == 1 and Uniform in terms:
                times, values = PiecewiseLinearCodeGen(self.assignments).visit(
                    terms[Uniform]
                )

                self.detuning = task_spec.Detuning(
                    global_=task_spec.GlobalField(times=times, values=values)
                )

            ## local detuning, no global
            case (Detuning(), Field(terms)) if len(terms) == 1:
                ((spatial_modulation, waveform),) = terms.items()

                times, values = PiecewiseLinearCodeGen(self.assignments).visit(waveform)

                self.visit(spatial_modulation)
                self.detuning = task_spec.Detuning(
                    global_=task_spec.GlobalField(
                        times=[0, times[-1]], values=[0.0, 0.0]
                    ),
                    local=task_spec.LocalField(
                        times=times,
                        values=values,
                        lattice_site_coefficients=self.lattice_site_coefficients,
                    ),
                )

            # local AND global detuning
            case (Detuning(), Field(terms)) if len(terms) == 2 and Uniform in terms:
                # will only be two keys
                for k in terms.keys():
                    if k == Uniform:
                        global_times, global_values = PiecewiseLinearCodeGen(
                            self.assignments
                        ).visit(terms[Uniform])
                    else:  # can be RunTimeVector or ScaledLocations
                        spatial_modulation = k
                        local_times, local_values = PiecewiseLinearCodeGen(
                            self.assignments
                        ).visit(terms[k])

                self.visit(spatial_modulation)  # just visit the non-uniform locations
                self.detuning = task_spec.Detuning(
                    local=task_spec.LocalField(
                        times=local_times,
                        values=local_values,
                        lattice_site_coefficients=self.lattice_site_coefficients,
                    ),
                    global_=task_spec.GlobalField(
                        times=global_times, values=global_values
                    ),
                )

            case _:
                raise NotImplementedError()

    def visit_pulse(self, ast: PulseExpr):
        match ast:
            case Pulse(fields):
                if RabiFrequencyAmplitude() in fields:
                    self.field_name = RabiFrequencyAmplitude()
                    self.visit(fields[self.field_name])

                if RabiFrequencyPhase() in fields:
                    self.field_name = RabiFrequencyPhase()
                    self.visit(fields[self.field_name])

                if Detuning() in fields:
                    self.field_name = Detuning()
                    self.visit(fields[self.field_name])

            case NamedPulse(pulse, _):
                self.visit(pulse)

            case _:
                raise ValueError(
                    "Failed to compile pulse expression to QuEra task, "
                    f"found: {repr(ast)}"
                )

        # fix-up any missing fields
        duration = 0.0

        if self.rabi_frequency_amplitude is not None:
            duration = max(duration, self.rabi_frequency_amplitude.global_.times[-1])

        if self.rabi_frequency_phase is not None:
            duration = max(duration, self.rabi_frequency_phase.global_.times[-1])

        if self.detuning is not None:
            duration = max(duration, self.detuning.global_.times[-1])

        if duration == 0.0:
            raise ValueError("No Fields found in pulse.")

        if self.rabi_frequency_amplitude is None:
            self.rabi_frequency_amplitude = task_spec.RabiFrequencyAmplitude(
                global_=task_spec.GlobalField(times=[0, duration], values=[0.0, 0.0])
            )

        if self.rabi_frequency_phase is None:
            self.rabi_frequency_phase = task_spec.RabiFrequencyPhase(
                global_=task_spec.GlobalField(times=[0, duration], values=[0.0, 0.0])
            )

        if self.detuning is None:
            self.detuning = task_spec.Detuning(
                global_=task_spec.GlobalField(times=[0, duration], values=[0.0, 0.0])
            )

        self.rydberg = task_spec.RydbergHamiltonian(
            rabi_frequency_amplitude=self.rabi_frequency_amplitude,
            rabi_frequency_phase=self.rabi_frequency_phase,
            detuning=self.detuning,
        )

    def visit_sequence(self, ast: SequenceExpr):
        match ast:
            case Sequence(pulses):
                if HyperfineLevelCoupling() in pulses:
                    raise ValueError("QuEra tasks does not support Hyperfine coupling.")

                self.visit(pulses[RydbergLevelCoupling()])

            case NamedSequence(sequence, _):
                self.visit(sequence)

            case _:
                raise ValueError(
                    "Failed to compile sequence expression to QuEra task, "
                    f"found: {repr(ast)}"
                )

        self.effective_hamiltonian = task_spec.EffectiveHamiltonian(
            rydberg=self.rydberg
        )

    def visit_lattice(self, ast: "Lattice"):
        sites = []
        filling = []
        for site in ast.enumerate():
            sites.append(tuple(site))
            filling.append(1)

        self.n_atoms = len(sites)
        self.lattice = task_spec.Lattice(sites=sites, filling=filling)

    def emit(self, nshots: int, ast: "Program") -> task_spec.QuEraTaskSpecification:
        # check if program has a multiplex section
        self.multiplex_mapping = ast.mapping

        # get proper variable assignments
        self.assignments = AssignmentScan(ast.assignments).emit(ast)

        self.visit(ast.lattice)

        self.visit(ast.seq)
        return task_spec.QuEraTaskSpecification(
            nshots=nshots,
            lattice=self.lattice,
            effective_hamiltonian=self.effective_hamiltonian,
        )
