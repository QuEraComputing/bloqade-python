from functools import cached_property
from bloqade.ir.scalar import Literal
import bloqade.ir.analog_circuit as analog_circuit
import bloqade.ir.control.field as field
import bloqade.ir.control.pulse as pulse
import bloqade.ir.control.sequence as sequence

import bloqade.ir.control.waveform as waveform
import bloqade.ir.location as location
from bloqade.ir.visitor import BloqadeIRVisitor

import bloqade.submission.ir.task_specification as task_spec
from bloqade.submission.ir.braket import BraketTaskSpecification
from bloqade.submission.ir.task_specification import QuEraTaskSpecification
from bloqade.submission.ir.parallel import ParallelDecoder, ClusterLocationInfo
from bloqade.submission.ir.capabilities import QuEraCapabilities
from bloqade.codegen.hardware.piecewise_linear import (
    PiecewiseLinearCodeGen,
    PiecewiseLinear,
)
from bloqade.codegen.hardware.piecewise_constant import (
    PiecewiseConstantCodeGen,
    PiecewiseConstant,
)

from typing import Any, Dict, Tuple, List, Union, Optional
from pydantic.dataclasses import dataclass
import numbers
from decimal import Decimal
import numpy as np


class GeneratePiecewiseLinearChannel(BloqadeIRVisitor):
    def __init__(
        self,
        level_coupling: sequence.LevelCoupling,
        field_name: pulse.FieldName,
        spatial_modulations: field.SpatialModulation,
    ):
        self.level_coupling = level_coupling
        self.field_name = field_name
        self.spatial_modulations = spatial_modulations

    def visit_waveform_Constant(self, node: waveform.Constant) -> PiecewiseLinear:
        return PiecewiseLinear(
            [Decimal(0), node.duration()], [node.value(), node.value()]
        )

    def visit_waveform_Linear(self, node: waveform.Linear) -> PiecewiseLinear:
        return PiecewiseLinear(
            [Decimal(0), node.duration()], [node.start(), node.stop()]
        )

    def visit_waveform_Poly(self, node: waveform.Poly) -> PiecewiseLinear:
        duration = node.duration()
        start = node.eval_decimal(0)
        stop = node.eval_decimal(duration)

        return PiecewiseLinear(
            [Decimal(0), duration],
            [start, stop],
        )

    def visit_waveform_Sample(self, node: waveform.Sample) -> PiecewiseLinear:
        times, values = node.samples()
        return PiecewiseLinear(times, values)

    def visit_waveform_Add(self, node: waveform.Add) -> PiecewiseLinear:
        lhs = self.visit(node.lhs)
        rhs = self.visit(node.rhs)

        times = sorted(list(set(lhs.times + rhs.times)))
        values = [lhs.eval(t) + rhs.eval(t) for t in times]

        return PiecewiseLinear(times, values)

    def visit_waveform_Append(self, node: waveform.Append) -> PiecewiseLinear:
        pwl = self.visit(node.waveforms[0])

        for wf in node.waveforms[1:]:
            pwl = pwl.append(self.visit(wf))

        return pwl

    def visit_waveform_Slice(self, node: waveform.Slice) -> PiecewiseLinear:
        pwl = self.visit(node.waveform)
        return pwl.slice(node.interval.start, node.interval.stop)

    def visit_waveform_Negative(self, node: waveform.Negative) -> PiecewiseLinear:
        pwl = self.visit(node.waveform)
        return PiecewiseLinear(pwl.times, [-v for v in pwl.values])

    def visit_waveform_Scale(self, node: waveform.Scale) -> PiecewiseLinear:
        pwl = self.visit(node.waveform)
        return PiecewiseLinear(pwl.times, [node.scalar() * v for v in pwl.values])

    def visit_field_Field(self, node: field.Field) -> PiecewiseLinear:
        return self.visit(node.drives[self.spatial_modulations])

    def visit_pulse_Pulse(self, node: pulse.Pulse) -> PiecewiseLinear:
        return self.visit(node.fields[self.field_name])

    def visit_pulse_NamedPulse(self, node: pulse.NamedPulse) -> PiecewiseLinear:
        return self.visit(node.pulse)

    def visit_pulse_Slice(self, node: pulse.Slice) -> PiecewiseLinear:
        start = node.interval.start()
        stop = node.interval.stop()

        pwl = self.visit(node.pulse)

        return pwl.slice(start, stop)

    def visit_pulse_Append(self, node: pulse.Append) -> PiecewiseLinear:
        pwl = self.visit(node.pulses[0])

        for p in node.pulses[1:]:
            pwl = pwl.append(self.visit(p))

        return pwl

    def visit_sequence_Sequence(self, node: sequence.Sequence) -> PiecewiseLinear:
        return self.visit(node.pulses[self.level_coupling])

    def visit_sequence_NamedSequence(
        self, node: sequence.NamedSequence
    ) -> PiecewiseLinear:
        return self.visit(node.sequence)

    def visit_sequence_Slice(self, node: sequence.Slice) -> PiecewiseLinear:
        start = node.interval.start()
        stop = node.interval.stop()

        pwl = self.visit(node.sequence)

        return pwl.slice(start, stop)

    def visit_sequence_Append(self, node: sequence.Append) -> PiecewiseLinear:
        pwl = self.visit(node.sequences[0])

        for seq in node.sequences[1:]:
            pwl = pwl.append(self.visit(seq))

        return pwl

    def visit_analog_circuit_AnalogCircuit(
        self, node: analog_circuit.AnalogCircuit
    ) -> PiecewiseLinear:
        return self.visit(node.sequence)


@dataclass(frozen=True)
class AHSCodegenResult:
    nshots: int
    parallel_decoder: Optional[ParallelDecoder]
    sites: List[Tuple[Decimal, Decimal]]
    filling: List[bool]
    global_detuning: PiecewiseLinear
    global_rabi_amplitude: PiecewiseLinear
    global_rabi_phase: PiecewiseConstant
    lattice_site_coefficients: Optional[List[Decimal]]
    local_detuning: Optional[PiecewiseLinear]

    def slice(self, start_time: Decimal, stop_time: Decimal) -> "AHSCodegenResult":
        return AHSCodegenResult(
            self.nshots,
            self.parallel_decoder,
            self.sites,
            self.filling,
            self.global_detuning.slice(start_time, stop_time),
            self.global_rabi_amplitude.slice(start_time, stop_time),
            self.global_rabi_phase.slice(start_time, stop_time),
            self.lattice_site_coefficients,
            self.local_detuning.slice(start_time, stop_time),
        )

    def append(self, other: "AHSCodegenResult") -> "AHSCodegenResult":
        assert self.nshots == other.nshots
        assert self.parallel_decoder == other.parallel_decoder
        assert self.sites == other.sites
        assert self.filling == other.filling
        assert self.lattice_site_coefficients == other.lattice_site_coefficients

        return AHSCodegenResult(
            self.nshots,
            self.parallel_decoder,
            self.sites,
            self.filling,
            self.global_detuning.append(other.global_detuning),
            self.global_rabi_amplitude.append(other.global_rabi_amplitude),
            self.global_rabi_phase.append(other.global_rabi_phase),
            self.lattice_site_coefficients,
            self.local_detuning.append(other.local_detuning),
        )

    @staticmethod
    def convert_position_units(position):
        return tuple(coordinate * Decimal("1e-6") for coordinate in position)

    @staticmethod
    def convert_time_units(time):
        return Decimal("1e-6") * time

    @staticmethod
    def convert_energy_units(energy):
        return Decimal("1e6") * energy

    @cached_property
    def braket_task_ir(self) -> BraketTaskSpecification:
        import braket.ir.ahs as ir

        return BraketTaskSpecification(
            nshots=self.nshots,
            program=ir.Program(
                setup=ir.Setup(
                    ahs_register=ir.AtomArrangement(
                        sites=list(map(self.convert_position_units, self.sites)),
                        filling=self.filling,
                    )
                ),
                hamiltonian=ir.Hamiltonian(
                    drivingFields=[
                        ir.DrivingField(
                            amplitude=ir.PhysicalField(
                                time_series=ir.TimeSeries(
                                    times=list(
                                        map(
                                            self.convert_time_units,
                                            self.global_rabi_amplitude.times,
                                        )
                                    ),
                                    values=list(
                                        map(
                                            self.convert_energy_units,
                                            self.global_rabi_amplitude.values,
                                        )
                                    ),
                                ),
                                pattern="uniform",
                            ),
                            phase=ir.PhysicalField(
                                time_series=ir.TimeSeries(
                                    times=list(
                                        map(
                                            self.convert_time_units,
                                            self.global_rabi_phase.times,
                                        )
                                    ),
                                    values=self.global_rabi_phase.values,
                                ),
                                pattern="uniform",
                            ),
                            detuning=ir.PhysicalField(
                                time_series=ir.TimeSeries(
                                    times=list(
                                        map(
                                            self.convert_time_units,
                                            self.global_detuning.times,
                                        )
                                    ),
                                    values=list(
                                        map(
                                            self.convert_energy_units,
                                            self.global_detuning.values,
                                        )
                                    ),
                                ),
                                pattern="uniform",
                            ),
                        )
                    ],
                    shiftingFields=(
                        []
                        if self.lattice_site_coefficients is None
                        else [
                            ir.ShiftingField(
                                magnitude=ir.PhysicalField(
                                    time_series=ir.TimeSeries(
                                        times=list(
                                            map(
                                                self.convert_time_units,
                                                self.local_detuning.times,
                                            )
                                        ),
                                        values=list(
                                            map(
                                                self.convert_energy_units,
                                                self.local_detuning.values,
                                            )
                                        ),
                                    ),
                                    pattern=self.lattice_site_coefficients,
                                )
                            )
                        ]
                    ),
                ),
            ),
        )

    @cached_property
    def quera_task_ir(self) -> QuEraTaskSpecification:
        import bloqade.submission.ir.task_specification as task_spec

        return task_spec.QuEraTaskSpecification(
            nshots=self.nshots,
            lattice=task_spec.Lattice(
                sites=list(map(self.convert_position_units, self.sites)),
                filling=self.filling,
            ),
            effective_hamiltonian=task_spec.EffectiveHamiltonian(
                rydberg=task_spec.RydbergHamiltonian(
                    rabi_frequency_amplitude=task_spec.RabiFrequencyAmplitude(
                        global_=task_spec.GlobalField(
                            times=list(
                                map(
                                    self.convert_time_units,
                                    self.global_rabi_amplitude.times,
                                )
                            ),
                            values=list(
                                map(
                                    self.convert_energy_units,
                                    self.global_rabi_amplitude.values,
                                )
                            ),
                        )
                    ),
                    rabi_frequency_phase=task_spec.RabiFrequencyPhase(
                        global_=task_spec.GlobalField(
                            times=list(
                                map(
                                    self.convert_time_units,
                                    self.global_rabi_phase.times,
                                )
                            ),
                            values=self.global_rabi_phase.values,
                        )
                    ),
                    detuning=task_spec.Detuning(
                        global_=task_spec.GlobalField(
                            times=list(
                                map(self.convert_time_units, self.global_detuning.times)
                            ),
                            values=list(
                                map(
                                    self.convert_energy_units,
                                    self.global_detuning.values,
                                )
                            ),
                        ),
                        local=(
                            None
                            if self.lattice_site_coefficients is None
                            else task_spec.LocalField(
                                times=list(
                                    map(
                                        self.convert_time_units,
                                        self.local_detuning.times,
                                    )
                                ),
                                values=list(
                                    map(
                                        self.convert_energy_units,
                                        self.local_detuning.values,
                                    )
                                ),
                                lattice_site_coefficients=self.lattice_site_coefficients,
                            )
                        ),
                    ),
                )
            ),
        )


class AHSCodegen(BloqadeIRVisitor):
    def __init__(
        self,
        shots: int,
        assignments: Dict[str, Union[numbers.Real, List[numbers.Real]]] = {},
        capabilities: Optional[QuEraCapabilities] = None,
    ):
        self.nshots = shots
        self.capabilities = capabilities
        self.assignments = assignments
        self.parallel_decoder = None
        self.sites = []
        self.filling = []
        self.global_detuning = None
        self.local_detuning = None
        self.lattice_site_coefficients = None
        self.global_rabi_amplitude = None
        self.global_rabi_phase = None

    def extract_fields(self, ahs_result: AHSCodegenResult) -> None:
        self.nshots = ahs_result.nshots
        self.sites = ahs_result.sites
        self.filling = ahs_result.filling
        self.global_detuning = ahs_result.global_detuning
        self.global_rabi_amplitude = ahs_result.global_rabi_amplitude
        self.global_rabi_phase = ahs_result.global_rabi_phase
        self.lattice_site_coefficients = ahs_result.lattice_site_coefficients
        self.local_detuning = ahs_result.local_detuning

    def fix_up_missing_fields(self) -> None:
        # fix-up any missing fields
        duration = 0.0

        if self.global_rabi_amplitude:
            duration = max(duration, self.global_rabi_amplitude.times[-1])

        if self.global_rabi_phase:
            duration = max(duration, self.global_rabi_phase.times[-1])

        if self.global_detuning:
            duration = max(duration, self.global_detuning.times[-1])

        if self.local_detuning:
            duration = max(duration, self.local_detuning.times[-1])

        if duration > 0:
            if self.global_rabi_amplitude is None:
                self.global_rabi_amplitude = PiecewiseLinear(
                    [Decimal(0), duration], [Decimal(0), Decimal(0)]
                )

            if self.global_rabi_phase is None:
                self.global_rabi_phase = PiecewiseConstant(
                    [Decimal(0), duration], [Decimal(0), Decimal(0)]
                )

            if self.global_detuning is None:
                self.global_detuning = PiecewiseLinear(
                    [Decimal(0), duration], [Decimal(0), Decimal(0)]
                )

        if self.local_detuning is None:
            pass

    def post_visit_spatial_modulation(self, lattice_site_coefficients):
        self.lattice_site_coefficients = []
        if self.parallel_decoder:
            for cluster_site_info in self.parallel_decoder.mapping:
                self.lattice_site_coefficients.append(
                    lattice_site_coefficients[cluster_site_info.cluster_location_index]
                )
        else:
            self.lattice_site_coefficients = lattice_site_coefficients

    def calculate_detuning(self, node: field.Field) -> Any:
        if len(node.drives) == 1 and field.Uniform in node.drives:
            self.global_detuning = PiecewiseLinearCodeGen(self.assignments).emit(
                node.drives[field.Uniform]
            )

        elif len(node.drives) == 1:
            ((spatial_modulation, waveform),) = node.drives.items()

            self.local_detuning = PiecewiseLinearCodeGen(self.assignments).emit(
                waveform
            )

            self.global_detuning = PiecewiseLinear(
                [Decimal(0), self.local_detuning.times[-1]], [Decimal(0), Decimal(0)]
            )

            self.visit(spatial_modulation)

        elif len(node.drives) == 2 and field.Uniform in node.drives:
            # will only be two keys
            for k in node.drives.keys():
                if k == field.Uniform:
                    self.global_detuning = PiecewiseLinearCodeGen(
                        self.assignments
                    ).emit(node.drives[field.Uniform])
                else:  # can be field.RunTimeVector or field.ScaledLocations
                    spatial_modulation = k
                    self.local_detuning = PiecewiseLinearCodeGen(self.assignments).emit(
                        node.drives[k]
                    )

            self.visit(spatial_modulation)  # just visit the non-uniform locations

        else:
            raise ValueError(
                "Failed to compile Detuning to QuEra task, "
                "found more than one non-uniform modulation: "
                f"{repr(node)}."
            )

    def calculate_rabi_amplitude(self, node: field.Field) -> Any:
        if len(node.drives) == 1 and field.Uniform in node.drives:
            self.global_rabi_amplitude = PiecewiseLinearCodeGen(self.assignments).emit(
                node.drives[field.Uniform]
            )

        else:
            raise ValueError(
                "Failed to compile Rabi Amplitude to QuEra task, "
                "found non-uniform modulation: "
                f"{repr(node)}."
            )

    def calculate_rabi_phase(self, node: field.Field) -> Any:
        if len(node.drives) == 1 and field.Uniform in node.drives:  # has to be global
            self.global_rabi_phase = PiecewiseConstantCodeGen(self.assignments).emit(
                node.drives[field.Uniform]
            )

        else:
            raise ValueError(
                "Failed to compile Rabi Phase to QuEra task, "
                "found non-uniform modulation: "
                f"{repr(node)}."
            )

    def visit_register(self, node: location.AtomArrangement):
        # default visitor for AtomArrangement
        self.sites = []
        self.filling = []

        for location_info in node.enumerate():
            site = tuple(ele(**self.assignments) for ele in location_info.position)
            self.sites.append(site)
            self.filling.append(location_info.filling.value)

        self.n_atoms = len(self.sites)

    #########################
    # Begin visitor methods #
    #########################

    def generic_visit(self, node):
        # dispatch all AtomArrangement nodes to visit_register
        # otherwise dispatch to super
        if isinstance(node, location.AtomArrangement):
            self.visit_register(node)

        super().generic_visit(node)

    def visit_field_Location(self, node: field.Location):
        if node.value >= self.n_atoms:
            raise ValueError(
                f"Location index out of bounds, found {node.value}"
                f" but with a register of size {self.n_atoms}."
            )

    def visit_analog_circuit_AnalogCircuit(
        self, node: analog_circuit.AnalogCircuit
    ) -> Any:
        self.visit(node.register)
        self.visit(node.sequence)

    def visit_field_Uniform(self, node: field.UniformModulation) -> Any:
        lattice_site_coefficients = [Decimal("1.0") for _ in range(self.n_atoms)]
        self.post_visit_spatial_modulation(lattice_site_coefficients)

    def visit_field_ScaledLocations(self, node: field.ScaledLocations) -> Any:
        lattice_site_coefficients = []

        for loc in node.value.keys():
            self.visit(loc)

        for atom_index in range(self.n_atoms):
            scale = node.value.get(field.Location(atom_index), Literal(0.0))
            lattice_site_coefficients.append(scale(**self.assignments))

        self.post_visit_spatial_modulation(lattice_site_coefficients)

    def visit_field_RunTimeVector(self, node: field.RunTimeVector) -> Any:
        if len(self.assignments[node.name]) != self.n_atoms:
            raise ValueError(
                f"Coefficient list {node.name} doesn't match the size of register "
                f"{self.n_atoms}."
            )
        lattice_site_coefficients = list(self.assignments[node.name])
        self.post_visit_spatial_modulation(lattice_site_coefficients)

    def visit_field_AssignedRunTimeVector(
        self, node: field.AssignedRunTimeVector
    ) -> Any:
        if len(node.value) != self.n_atoms:
            raise ValueError(
                f"Coefficient list {node.name} doesn't match the size of register "
                f"{self.n_atoms}."
            )
        lattice_site_coefficients = node.value
        self.post_visit_spatial_modulation(lattice_site_coefficients)

    def visit_field_Field(self, node: field.Field):
        if self.field_name == pulse.detuning:
            self.calculate_detuning(node)
        elif self.field_name == pulse.rabi.amplitude:
            self.calculate_rabi_amplitude(node)
        elif self.field_name == pulse.rabi.phase:
            self.calculate_rabi_phase(node)

    def visit_pulse_Pulse(self, node: pulse.Pulse):
        for field_name in node.fields.keys():
            self.field_name = field_name
            self.visit(node.fields[field_name])

    def visit_pulse_NamedNulse(self, node: pulse.NamedPulse):
        self.visit(node.pulse)

    def visit_pulse_Append(self, node: pulse.Append):
        subexpr_compiler = AHSCodegen(self.nshots, self.assignments)
        ahs_result = subexpr_compiler.emit(node.pulses)

        for seq in node.sequences:
            new_ahs_result = subexpr_compiler.emit(seq)
            ahs_result = ahs_result.append(new_ahs_result)

        self.extract_fields(ahs_result)

    def visit_pulse_Slice(self, node: pulse.Slice):
        start_time = node.interval.start(**self.assignments)
        stop_time = node.interval.stop(**self.assignments)

        ahs_result = AHSCodegen(self.nshots, self.assignments).emit(node.pulse)
        ahs_result = ahs_result.slice(start_time, stop_time)

        self.extract_fields(ahs_result)

    def visit_sequence_Sequence(self, node: sequence.Sequence):
        if sequence.HyperfineLevelCoupling() in node.pulses:
            raise ValueError("QuEra tasks does not support Hyperfine coupling.")

        self.visit(node.pulses.get(sequence.RydbergLevelCoupling(), pulse.Pulse({})))

    def visit_sequence_Append(self, node: sequence.Append):
        subexpr_compiler = AHSCodegen(self.nshots, self.assignments)
        ahs_result = subexpr_compiler.emit(node.sequences[0])

        for sub_sequence in node.sequences[1:]:
            new_ahs_result = subexpr_compiler.emit(sub_sequence)
            ahs_result = ahs_result.append(new_ahs_result)

        self.extract_fields(ahs_result)

    def visit_sequence_Slice(self, node: sequence.Slice):
        start_time = node.interval.start(**self.assignments)
        stop_time = node.interval.stop(**self.assignments)

        ahs_result = AHSCodegen(self.nshots, self.assignments).emit(node.sequence)
        ahs_result = ahs_result.slice(start_time, stop_time)
        self.extract_fields(ahs_result)

    def visit_location_ParallelRegister(self, node: location.ParallelRegister) -> Any:
        info = node.info
        if self.capabilities is None:
            raise NotImplementedError(
                "Cannot parallelize register without device capabilities."
            )

        height_max = self.capabilities.capabilities.lattice.area.height / Decimal(
            "1e-6"
        )
        width_max = self.capabilities.capabilities.lattice.area.width / Decimal("1e-6")
        number_sites_max = (
            self.capabilities.capabilities.lattice.geometry.number_sites_max
        )

        register_filling = np.asarray(info.register_filling)

        register_locations = np.asarray(
            [
                [s(**self.assignments) for s in location]
                for location in info.register_locations
            ]
        )
        register_locations = register_locations - register_locations.min(axis=0)

        shift_vectors = np.asarray(
            [
                [s(**self.assignments) for s in shift_vector]
                for shift_vector in info.shift_vectors
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
            if len(mapping) + len(info.register_locations) > number_sites_max:
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

            for cluster_location_index, (loc, filled) in enumerate(
                zip(new_register_locations[:], register_filling)
            ):
                site = tuple(loc)
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
        self.n_atoms = len(info.register_locations)
        self.parallel_decoder = ParallelDecoder(mapping=mapping)

    def emit(self, node) -> AHSCodegenResult:
        self.visit(node)
        self.fix_up_missing_fields()

        if all(  # TODO: move this into analysis portion.
            [
                self.global_detuning is None,
                self.global_rabi_amplitude is None,
                self.global_rabi_phase is None,
                self.local_detuning is None,
            ]
        ):
            raise ValueError("No fields were specified.")

        return AHSCodegenResult(
            nshots=self.nshots,
            parallel_decoder=self.parallel_decoder,
            sites=self.sites,
            filling=self.filling,
            global_detuning=self.global_detuning,
            global_rabi_amplitude=self.global_rabi_amplitude,
            global_rabi_phase=self.global_rabi_phase,
            lattice_site_coefficients=self.lattice_site_coefficients,
            local_detuning=self.local_detuning,
        )
