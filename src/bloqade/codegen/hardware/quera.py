from bloqade.ir.analog_circuit import AnalogCircuit
from bloqade.ir.scalar import Literal
import bloqade.ir.control.waveform as waveform
import bloqade.ir.control.field as field
import bloqade.ir.control.pulse as pulse
import bloqade.ir.control.sequence as sequence

from bloqade.ir.location.base import AtomArrangement, ParallelRegister
from bloqade.ir.control.waveform import Record

from bloqade.ir.visitor.analog_circuit import AnalogCircuitVisitor
from bloqade.ir.visitor.waveform import WaveformVisitor

import bloqade.submission.ir.task_specification as task_spec
from bloqade.submission.ir.parallel import ParallelDecoder, ClusterLocationInfo
from bloqade.submission.ir.capabilities import QuEraCapabilities

from typing import Any, Dict, Tuple, List, Union, Optional
from bisect import bisect_left
import numbers
from decimal import Decimal
import numpy as np


class PiecewiseLinearCodeGen(WaveformVisitor):
    def __init__(self, assignments: Dict[str, Union[numbers.Real, List[numbers.Real]]]):
        self.assignments = assignments

    def visit_negative(
        self, ast: waveform.Negative
    ) -> Tuple[List[Decimal], List[Decimal]]:
        times, values = self.visit(ast.waveform)
        return times, [-value for value in values]

    def visit_scale(self, ast: waveform.Scale) -> Tuple[List[Decimal], List[Decimal]]:
        times, values = self.visit(ast.waveform)
        scaler = ast.scalar(**self.assignments)
        return times, [scaler * value for value in values]

    def visit_linear(self, ast: waveform.Linear) -> Tuple[List[Decimal], List[Decimal]]:
        duration = ast.duration(**self.assignments)
        start = ast.start(**self.assignments)
        stop = ast.stop(**self.assignments)

        return [Decimal(0), duration], [start, stop]

    def visit_constant(
        self, ast: waveform.Constant
    ) -> Tuple[List[Decimal], List[Decimal]]:
        duration = ast.duration(**self.assignments)
        value = ast.value(**self.assignments)

        return [Decimal(0), duration], [value, value]

    def visit_poly(self, ast: waveform.Poly) -> Tuple[List[Decimal], List[Decimal]]:
        if len(ast.coeffs) == 1:
            duration = ast.duration(**self.assignments)
            value = ast.coeffs[0](**self.assignments)
            return [Decimal(0), duration], [value, value]

        if len(ast.coeffs) == 2:
            duration = ast.duration(**self.assignments)
            start = ast.coeffs[0](**self.assignments)
            stop = start + ast.coeffs[1](**self.assignments) * duration

            return [Decimal(0), duration], [start, stop]

        order = len(ast.coeffs) - 1

        raise ValueError(
            "Failed to compile Waveform to piecewise linear,"
            f"found Polynomial of order {order}."
        )

    def visit_slice(self, ast: waveform.Slice) -> Tuple[List[Decimal], List[Decimal]]:
        duration = ast.waveform.duration(**self.assignments)
        if ast.interval.start is None:
            start_time = Decimal(0)
        else:
            start_time = ast.interval.start(**self.assignments)

        if ast.interval.stop is None:
            stop_time = duration
        else:
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

        if start_time == stop_time:
            return [Decimal(0.0), Decimal(0.0)], [Decimal(0.0), Decimal(0.0)]

        times, values = self.visit(ast.waveform)

        start_index = bisect_left(times, start_time)
        stop_index = bisect_left(times, stop_time)
        start_value = ast.waveform.eval_decimal(start_time, **self.assignments)
        stop_value = ast.waveform.eval_decimal(stop_time, **self.assignments)

        if start_index == 0:
            if stop_time == duration:
                absolute_times = times
                values = values
            else:
                absolute_times = times[:stop_index] + [stop_time]
                values = values[:stop_index] + [stop_value]
        elif start_time == times[start_index]:
            if stop_time == duration:
                absolute_times = times[start_index:]
                values = values[start_index:]
            else:
                absolute_times = times[start_index:stop_index] + [stop_time]
                values = values[start_index:stop_index] + [stop_value]
        else:
            if stop_time == duration:
                absolute_times = [start_time] + times[start_index:]
                values = [start_value] + values[start_index:]
            else:
                absolute_times = (
                    [start_time] + times[start_index:stop_index] + [stop_time]
                )
                values = [start_value] + values[start_index:stop_index] + [stop_value]

        times = [time - start_time for time in absolute_times]

        return times, values

    def visit_append(self, ast: waveform.Append) -> Tuple[List[Decimal], List[Decimal]]:
        times, values = self.visit(ast.waveforms[0])

        for sub_expr in ast.waveforms[1:]:
            new_times, new_values = self.visit(sub_expr)

            # skip instructions with duration=0
            if new_times[-1] == Decimal(0):
                continue
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

    def visit_sample(self, ast: waveform.Sample) -> Tuple[List[Decimal], List[Decimal]]:
        if ast.interpolation is not waveform.Interpolation.Linear:
            raise ValueError(
                "Failed to compile waveform to piecewise linear, "
                f"found piecewise {ast.interpolation.value} interpolation."
            )
        return ast.samples(**self.assignments)

    def visit_record(self, ast: Record) -> Tuple[List[Decimal], List[Decimal]]:
        return self.visit(ast.waveform)


class PiecewiseConstantCodeGen(WaveformVisitor):
    def __init__(self, assignments: Dict[str, Union[numbers.Real, List[numbers.Real]]]):
        self.assignments = assignments

    def visit_negative(
        self, ast: waveform.Negative
    ) -> Tuple[List[Decimal], List[Decimal]]:
        times, values = self.visit(ast.waveform)
        return times, [-value for value in values]

    def visit_scale(self, ast: waveform.Scale) -> Tuple[List[Decimal], List[Decimal]]:
        times, values = self.visit(ast.waveform)
        scaler = ast.scalar(**self.assignments)
        return times, [scaler * value for value in values]

    def visit_linear(self, ast: waveform.Linear) -> Tuple[List[Decimal], List[Decimal]]:
        duration = ast.duration(**self.assignments)
        start = ast.start(**self.assignments)
        stop = ast.stop(**self.assignments)

        if start != stop:
            raise ValueError(
                "Failed to compile Waveform to piecewise constant, "
                "found non-constant Linear piecce."
            )

        return [0, duration], [start, stop]

    def visit_constant(
        self, ast: waveform.Constant
    ) -> Tuple[List[Decimal], List[Decimal]]:
        duration = ast.duration(**self.assignments)
        value = ast.value(**self.assignments)

        return [Decimal(0), duration], [value, value]

    def visit_poly(self, ast: waveform.Poly) -> Tuple[List[Decimal], List[Decimal]]:
        if len(ast.coeffs) == 1:
            duration = ast.duration(**self.assignments)
            value = ast.coeffs[0](**self.assignments)
            return [Decimal(0), duration], [value, value]

        if len(ast.coeffs) == 2:
            duration = ast.duration(**self.assignments)
            start = ast.coeffs[0](**self.assignments)
            stop = start + ast.coeffs[1](**self.assignments) * duration

            if start != stop:
                raise ValueError(
                    "Failed to compile Waveform to piecewise constant, "
                    "found non-constant Polynomial piece."
                )

            return [Decimal(0), duration], [start, stop]

        order = len(ast.coeffs) - 1

        raise ValueError(
            "Failed to compile Waveform to piecewise constant,"
            f"found Polynomial of order {order}."
        )

    def visit_slice(self, ast: waveform.Slice) -> Tuple[List[Decimal], List[Decimal]]:
        duration = ast.waveform.duration(**self.assignments)
        if ast.interval.start is None:
            start_time = Decimal(0)
        else:
            start_time = ast.interval.start(**self.assignments)

        if ast.interval.stop is None:
            stop_time = duration
        else:
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

        if start_time == stop_time:
            return [Decimal(0.0), Decimal(0.0)], [Decimal(0.0), Decimal(0.0)]

        times, values = self.visit(ast.waveform)

        start_index = bisect_left(times, start_time)
        stop_index = bisect_left(times, stop_time)

        if start_index == 0:
            if stop_time == duration:
                absolute_times = times
                values = values
            else:
                absolute_times = times[:stop_index] + [stop_time]
                values = values[:stop_index] + [values[stop_index - 1]]
        elif start_time == times[start_index]:
            if stop_time == duration:
                absolute_times = times[start_index:]
                values = values[start_index:]
            else:
                absolute_times = times[start_index:stop_index] + [stop_time]
                values = values[start_index:stop_index] + [values[stop_index - 1]]
        else:
            if stop_time == duration:
                absolute_times = [start_time] + times[start_index:]
                values = [values[start_index - 1]] + values[start_index:]
            else:
                absolute_times = (
                    [start_time] + times[start_index:stop_index] + [stop_time]
                )
                values = (
                    [values[start_index - 1]]
                    + values[start_index:stop_index]
                    + [values[stop_index - 1]]
                )

        times = [time - start_time for time in absolute_times]

        return times, values

    def visit_append(self, ast: waveform.Append) -> Tuple[List[Decimal], List[Decimal]]:
        times, values = self.visit(ast.waveforms[0])

        for sub_expr in ast.waveforms[1:]:
            new_times, new_values = self.visit(sub_expr)

            # skip instructions with duration=0
            if new_times[-1] == Decimal(0):
                continue

            shifted_times = [time + times[-1] for time in new_times[1:]]
            times.extend(shifted_times)
            values[-1] = new_values[0]
            values.extend(new_values[1:])

        return times, values

    def visit_sample(self, ast: waveform.Sample) -> Tuple[List[Decimal], List[Decimal]]:
        if ast.interpolation is not waveform.Interpolation.Constant:
            raise ValueError(
                "Failed to compile waveform to piecewise constant, "
                f"found piecewise {ast.interpolation.value} interpolation."
            )
        times, values = ast.samples(**self.assignments)

        values[-1] = values[-2]
        return times, values

    def visit_record(self, ast: Record) -> Tuple[List[Decimal], List[Decimal]]:
        return self.visit(ast.waveform)


class QuEraCodeGen(AnalogCircuitVisitor):
    def __init__(
        self,
        assignments: Dict[str, Union[numbers.Real, List[numbers.Real]]] = {},
        capabilities: Optional[QuEraCapabilities] = None,
    ):
        self.capabilities = capabilities
        self.assignments = assignments
        self.parallel_decoder = None
        self.lattice = None
        self.effective_hamiltonian = None
        self.rydberg = None
        self.field_name = None
        self.rabi_frequency_amplitude = None
        self.rabi_frequency_phase = None
        self.detuning = None
        self.lattice_site_coefficients = None

    @staticmethod
    def convert_time_to_SI_units(times: List[Decimal]):
        return [time * Decimal("1e-6") for time in times]

    @staticmethod
    def convert_energy_to_SI_units(values: List[Decimal]):
        return [value * Decimal("1e6") for value in values]

    @staticmethod
    def convert_position_to_SI_units(position: Tuple[Decimal]):
        return tuple(coordinate * Decimal("1e-6") for coordinate in position)

    def post_visit_spatial_modulation(self, lattice_site_coefficients):
        self.lattice_site_coefficients = []
        if self.parallel_decoder:
            for cluster_site_info in self.parallel_decoder.mapping:
                self.lattice_site_coefficients.append(
                    lattice_site_coefficients[cluster_site_info.cluster_location_index]
                )
        else:
            self.lattice_site_coefficients = lattice_site_coefficients

    def visit_location(self, ast: field.Location) -> Any:
        if (
            ast.value >= self.n_atoms
        ):  # n_atoms is now the number of atoms in the parallelized
            # lattice, but needs to be num. atoms in the original
            raise ValueError(
                f"field.Location({ast.value}) is larger than the register."
            )

    def visit_uniform_modulation(self, ast: field.UniformModulation) -> Any:
        lattice_site_coefficients = [Decimal("1.0") for _ in range(self.n_atoms)]
        self.post_visit_spatial_modulation(lattice_site_coefficients)

    def visit_scaled_locations(self, ast: field.ScaledLocations) -> Any:
        lattice_site_coefficients = []

        for location in ast.value.keys():
            self.visit(location)

        for atom_index in range(self.n_atoms):
            scale = ast.value.get(field.Location(atom_index), Literal(0.0))
            lattice_site_coefficients.append(scale(**self.assignments))

        self.post_visit_spatial_modulation(lattice_site_coefficients)

    def visit_run_time_vector(self, ast: field.RunTimeVector) -> Any:
        if len(self.assignments[ast.name]) != self.n_atoms:
            raise ValueError(
                f"Coefficient list {ast.name} doesn't match the size of register "
                f"{self.n_atoms}."
            )
        lattice_site_coefficients = list(self.assignments[ast.name])
        self.post_visit_spatial_modulation(lattice_site_coefficients)

    def visit_assigned_run_time_vector(self, ast: field.AssignedRunTimeVector) -> Any:
        if len(ast.value) != self.n_atoms:
            raise ValueError(
                f"Coefficient list {ast.name} doesn't match the size of register "
                f"{self.n_atoms}."
            )
        lattice_site_coefficients = ast.value
        self.post_visit_spatial_modulation(lattice_site_coefficients)

    def visit_detuning(self, ast: field.Field) -> Any:
        if len(ast.value) == 1 and field.Uniform in ast.value:
            times, values = PiecewiseLinearCodeGen(self.assignments).visit(
                ast.value[field.Uniform]
            )

            times = QuEraCodeGen.convert_time_to_SI_units(times)
            values = QuEraCodeGen.convert_energy_to_SI_units(values)

            self.detuning = task_spec.Detuning(
                global_=task_spec.GlobalField(times=times, values=values)
            )
        elif len(ast.value) == 1:
            ((spatial_modulation, waveform),) = ast.value.items()

            times, values = PiecewiseLinearCodeGen(self.assignments).visit(waveform)

            times = QuEraCodeGen.convert_time_to_SI_units(times)
            values = QuEraCodeGen.convert_energy_to_SI_units(values)

            self.visit(spatial_modulation)
            self.detuning = task_spec.Detuning(
                global_=task_spec.GlobalField(times=[0, times[-1]], values=[0.0, 0.0]),
                local=task_spec.LocalField(
                    times=times,
                    values=values,
                    lattice_site_coefficients=self.lattice_site_coefficients,
                ),
            )
        elif len(ast.value) == 2 and field.Uniform in ast.value:
            # will only be two keys
            for k in ast.value.keys():
                if k == field.Uniform:
                    global_times, global_values = PiecewiseLinearCodeGen(
                        self.assignments
                    ).visit(ast.value[field.Uniform])
                else:  # can be field.RunTimeVector or field.ScaledLocations
                    spatial_modulation = k
                    local_times, local_values = PiecewiseLinearCodeGen(
                        self.assignments
                    ).visit(ast.value[k])

            self.visit(spatial_modulation)  # just visit the non-uniform locations

            global_times = QuEraCodeGen.convert_time_to_SI_units(global_times)
            local_times = QuEraCodeGen.convert_time_to_SI_units(local_times)

            global_values = QuEraCodeGen.convert_energy_to_SI_units(global_values)
            local_values = QuEraCodeGen.convert_energy_to_SI_units(local_values)

            self.detuning = task_spec.Detuning(
                local=task_spec.LocalField(
                    times=local_times,
                    values=local_values,
                    lattice_site_coefficients=self.lattice_site_coefficients,
                ),
                global_=task_spec.GlobalField(times=global_times, values=global_values),
            )
        else:
            raise ValueError(
                "Failed to compile Detuning to QuEra task, "
                "found more than one non-uniform modulation: "
                f"{repr(ast)}."
            )

    def visit_rabi_amplitude(self, ast: field.Field) -> Any:
        if len(ast.value) == 1 and field.Uniform in ast.value:
            times, values = PiecewiseLinearCodeGen(self.assignments).visit(
                ast.value[field.Uniform]
            )

            times = QuEraCodeGen.convert_time_to_SI_units(times)
            values = QuEraCodeGen.convert_energy_to_SI_units(values)

            self.rabi_frequency_amplitude = task_spec.RabiFrequencyAmplitude(
                global_=task_spec.GlobalField(times=times, values=values)
            )
        else:
            raise ValueError(
                "Failed to compile Rabi Amplitude to QuEra task, "
                "found non-uniform modulation: "
                f"{repr(ast)}."
            )

    def visit_rabi_phase(self, ast: field.Field) -> Any:
        if len(ast.value) == 1 and field.Uniform in ast.value:  # has to be global
            times, values = PiecewiseConstantCodeGen(self.assignments).visit(
                ast.value[field.Uniform]
            )

            times = QuEraCodeGen.convert_time_to_SI_units(times)

            self.rabi_frequency_phase = task_spec.RabiFrequencyAmplitude(
                global_=task_spec.GlobalField(times=times, values=values)
            )
        else:
            raise ValueError(
                "Failed to compile Rabi Phase to QuEra task, "
                "found non-uniform modulation: "
                f"{repr(ast)}."
            )

    def visit_field(self, ast: field.Field):
        if self.field_name == pulse.detuning:
            self.visit_detuning(ast)
        elif self.field_name == pulse.rabi.amplitude:
            self.visit_rabi_amplitude(ast)
        elif self.field_name == pulse.rabi.phase:
            self.visit_rabi_phase(ast)

    def visit_pulse(self, ast: pulse.Pulse):
        for field_name in ast.fields.keys():
            self.field_name = field_name
            self.visit(ast.fields[field_name])

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

    def visit_named_pulse(self, ast: pulse.NamedPulse):
        self.visit(ast.pulse)

    def visit_append_pulse(self, ast: pulse.Append):
        raise NotImplementedError(
            "Failed to compile Append to QuEra task, "
            "found non-atomic pulse expression: "
            f"{repr(ast)}."
        )

    def visit_slice_pulse(self, ast: pulse.Append):
        raise NotImplementedError(
            "Failed to compile Append to QuEra task, "
            "found non-atomic pulse expression: "
            f"{repr(ast)}."
        )

    def visit_sequence(self, ast: sequence.Sequence):
        if sequence.HyperfineLevelCoupling() in ast.pulses:
            raise ValueError("QuEra tasks does not support Hyperfine coupling.")

        self.visit(ast.pulses.get(sequence.RydbergLevelCoupling(), pulse.Pulse({})))
        self.effective_hamiltonian = task_spec.EffectiveHamiltonian(
            rydberg=self.rydberg
        )

    def visit_named_sequence(self, ast: sequence.NamedSequence):
        self.visit(ast.sequence)

    def visit_append_sequence(self, ast: sequence.Append):
        raise NotImplementedError(
            "Failed to compile Append to QuEra task, "
            "found non-atomic sequence expression: "
            f"{repr(ast)}."
        )

    def visit_slice_sequence(self, ast: sequence.Slice):
        raise NotImplementedError(
            "Failed to compile Slice to QuEra task, "
            "found non-atomic sequence expression: "
            f"{repr(ast)}."
        )

    def visit_register(self, ast: AtomArrangement):
        sites = []
        filling = []

        for location_info in ast.enumerate():
            site = tuple(ele(**self.assignments) for ele in location_info.position)
            sites.append(QuEraCodeGen.convert_position_to_SI_units(site))
            filling.append(location_info.filling.value)

        self.n_atoms = len(sites)

        self.lattice = task_spec.Lattice(sites=sites, filling=filling)

    def visit_parallel_register(self, ast: ParallelRegister) -> Any:
        if self.capabilities is None:
            raise NotImplementedError(
                "Cannot parallelize register without device capabilities."
            )

        height_max = self.capabilities.capabilities.lattice.area.height / 1e-6
        width_max = self.capabilities.capabilities.lattice.area.width / 1e-6
        number_sites_max = (
            self.capabilities.capabilities.lattice.geometry.number_sites_max
        )

        register_filling = np.asarray(ast.register_filling)

        register_locations = np.asarray(
            [
                [s(**self.assignments) for s in location]
                for location in ast.register_locations
            ]
        )
        register_locations = register_locations - register_locations.min(axis=0)

        shift_vectors = np.asarray(
            [
                [s(**self.assignments) for s in shift_vector]
                for shift_vector in ast.shift_vectors
            ]
        )

        # build register by stack method because
        # shift_vectors might not be rectangular
        c_stack = [(0, 0)]
        visited = set([(0, 0)])
        mapping = []
        global_site_index = 0
        sites = []
        filling = []
        while c_stack:
            if len(mapping) + len(ast.register_locations) > number_sites_max:
                break

            cluster_index = c_stack.pop()

            shift = (
                shift_vectors[0] * cluster_index[0]
                + shift_vectors[1] * cluster_index[1]
            )

            new_register_locations = register_locations + shift

            # skip clusters that fall out of bounds
            if (
                np.any(new_register_locations < 0)
                or np.any(new_register_locations[:, 0] > width_max)
                or np.any(new_register_locations[:, 1] > height_max)
            ):
                continue

            new_cluster_indices = [
                (cluster_index[0] + 1, cluster_index[1]),
                (cluster_index[0], cluster_index[1] + 1),
                (cluster_index[0] - 1, cluster_index[1]),
                (cluster_index[0], cluster_index[1] - 1),
            ]

            for new_cluster_index in new_cluster_indices:
                if new_cluster_index not in visited:
                    visited.add(new_cluster_index)
                    c_stack.append(new_cluster_index)

            for cluster_location_index, (location, filled) in enumerate(
                zip(new_register_locations[:], register_filling)
            ):
                site = QuEraCodeGen.convert_position_to_SI_units(tuple(location))
                sites.append(site)
                filling.append(filled)

                mapping.append(
                    ClusterLocationInfo(
                        cluster_index=cluster_index,
                        global_location_index=global_site_index,
                        cluster_location_index=cluster_location_index,
                    )
                )

                global_site_index += 1

        self.lattice = task_spec.Lattice(sites=sites, filling=filling)
        self.n_atoms = len(ast.register_locations)
        self.parallel_decoder = ParallelDecoder(mapping=mapping)

    def visit_analog_circuit(self, ast: AnalogCircuit) -> Any:
        self.visit(ast.register)
        self.visit(ast.sequence)

    def emit(
        self, nshots: int, analog_circuit: AnalogCircuit
    ) -> Tuple[task_spec.QuEraTaskSpecification, Optional[ParallelDecoder]]:
        self.visit(analog_circuit)

        task_ir = task_spec.QuEraTaskSpecification(
            nshots=nshots,
            lattice=self.lattice,
            effective_hamiltonian=self.effective_hamiltonian,
        )

        return task_ir, self.parallel_decoder
