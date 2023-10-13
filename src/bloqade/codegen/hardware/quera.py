from functools import cached_property
from bloqade.ir.analog_circuit import AnalogCircuit
from bloqade.ir.scalar import Literal
import bloqade.ir.control.field as field
import bloqade.ir.control.pulse as pulse
import bloqade.ir.control.sequence as sequence

from bloqade.ir.location.base import AtomArrangement, ParallelRegister
from bloqade.ir.visitor.analog_circuit import AnalogCircuitVisitor

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

    @cached_property
    def braket_task_ir(self) -> BraketTaskSpecification:
        import braket.ir.ahs as ir

        def convert_time_units(time):
            return Decimal("1e-6") * time

        def convert_energy_units(energy):
            return Decimal("1e6") * energy

        return BraketTaskSpecification(
            nshots=self.nshots,
            program=ir.Program(
                setup=ir.Setup(
                    ahs_register=ir.AtomArrangement(
                        sites=self.sites, filling=self.filling
                    )
                ),
                hamiltonian=ir.Hamiltonian(
                    drivingFields=[
                        ir.DrivingField(
                            amplitude=ir.PhysicalField(
                                time_series=ir.TimeSeries(
                                    times=list(
                                        map(
                                            convert_time_units,
                                            self.global_rabi_amplitude.times,
                                        )
                                    ),
                                    values=list(
                                        map(
                                            convert_energy_units,
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
                                            convert_time_units,
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
                                            convert_time_units,
                                            self.global_detuning.times,
                                        )
                                    ),
                                    values=list(
                                        map(
                                            convert_energy_units,
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
                                amplitude=ir.PhysicalField(
                                    time_series=ir.TimeSeries(
                                        times=list(
                                            map(
                                                convert_time_units,
                                                self.local_detuning.times,
                                            )
                                        ),
                                        values=list(
                                            map(
                                                convert_energy_units,
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

        def convert_time_units(time):
            return Decimal("1e-6") * time

        def convert_energy_units(energy):
            return Decimal("1e6") * energy

        return task_spec.QuEraTaskSpecification(
            nshots=self.nshots,
            lattice=task_spec.Lattice(sites=self.sites, filling=self.filling),
            effective_hamiltonian=task_spec.EffectiveHamiltonian(
                rydberg=task_spec.RydbergHamiltonian(
                    rabi_frequency_amplitude=task_spec.RabiFrequencyAmplitude(
                        global_=task_spec.GlobalField(
                            times=list(
                                map(
                                    convert_time_units, self.global_rabi_amplitude.times
                                )
                            ),
                            values=list(
                                map(
                                    convert_energy_units,
                                    self.global_rabi_amplitude.values,
                                )
                            ),
                        )
                    ),
                    rabi_frequency_phase=task_spec.RabiFrequencyPhase(
                        global_=task_spec.GlobalField(
                            times=list(
                                map(convert_time_units, self.global_rabi_phase.times)
                            ),
                            values=self.global_rabi_phase.values,
                        )
                    ),
                    detuning=task_spec.Detuning(
                        global_=task_spec.GlobalField(
                            times=list(
                                map(convert_time_units, self.global_detuning.times)
                            ),
                            values=list(
                                map(convert_energy_units, self.global_detuning.values)
                            ),
                        ),
                        local=(
                            None
                            if self.lattice_site_coefficients is None
                            else task_spec.LocalField(
                                times=list(
                                    map(convert_time_units, self.local_detuning.times)
                                ),
                                values=list(
                                    map(
                                        convert_energy_units, self.local_detuning.values
                                    )
                                ),
                                lattice_site_coefficients=self.lattice_site_coefficients,
                            )
                        ),
                    ),
                )
            ),
        )


class AHSCodegen(AnalogCircuitVisitor):
    def __init__(
        self,
        shots: int,
        assignments: Dict[str, Union[numbers.Real, List[numbers.Real]]] = {},
        capabilities: Optional[QuEraCapabilities] = None,
    ):
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

    def calculate_detuning(self, ast: field.Field) -> Any:
        if len(ast.drives) == 1 and field.Uniform in ast.drives:
            self.global_detuning = PiecewiseLinearCodeGen(self.assignments).emit(
                ast.drives[field.Uniform]
            )

        elif len(ast.drives) == 1:
            ((spatial_modulation, waveform),) = ast.drives.items()

            self.local_detuning = PiecewiseLinearCodeGen(self.assignments).emit(
                waveform
            )

            self.global_detuning = PiecewiseLinear(
                [Decimal(0), self.local_detuning.times[-1]], [Decimal(0), Decimal(0)]
            )

            self.visit(spatial_modulation)

        elif len(ast.drives) == 2 and field.Uniform in ast.drives:
            # will only be two keys
            for k in ast.drives.keys():
                if k == field.Uniform:
                    self.global_detuning = PiecewiseLinearCodeGen(
                        self.assignments
                    ).emit(ast.drives[field.Uniform])
                else:  # can be field.RunTimeVector or field.ScaledLocations
                    spatial_modulation = k
                    self.local_detuning = PiecewiseLinearCodeGen(self.assignments).emit(
                        ast.drives[k]
                    )

            self.visit(spatial_modulation)  # just visit the non-uniform locations

        else:
            raise ValueError(
                "Failed to compile Detuning to QuEra task, "
                "found more than one non-uniform modulation: "
                f"{repr(ast)}."
            )

    def calculate_rabi_amplitude(self, ast: field.Field) -> Any:
        if len(ast.drives) == 1 and field.Uniform in ast.drives:
            self.global_rabi_amplitude = PiecewiseLinearCodeGen(self.assignments).emit(
                ast.drives[field.Uniform]
            )

        else:
            raise ValueError(
                "Failed to compile Rabi Amplitude to QuEra task, "
                "found non-uniform modulation: "
                f"{repr(ast)}."
            )

    def calculate_rabi_phase(self, ast: field.Field) -> Any:
        if len(ast.drives) == 1 and field.Uniform in ast.drives:  # has to be global
            self.global_rabi_phase = PiecewiseConstantCodeGen(self.assignments).emit(
                ast.drives[field.Uniform]
            )

        else:
            raise ValueError(
                "Failed to compile Rabi Phase to QuEra task, "
                "found non-uniform modulation: "
                f"{repr(ast)}."
            )

    def visit_field(self, ast: field.Field):
        if self.field_name == pulse.detuning:
            self.calculate_detuning(ast)
        elif self.field_name == pulse.rabi.amplitude:
            self.calculate_rabi_amplitude(ast)
        elif self.field_name == pulse.rabi.phase:
            self.calculate_rabi_phase(ast)

    def visit_pulse(self, ast: pulse.Pulse):
        for field_name in ast.fields.keys():
            self.field_name = field_name
            self.visit(ast.fields[field_name])

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

        if duration == Decimal(0):
            raise ValueError("No Fields found in pulse.")

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
        self.sites = []
        self.filling = []

        for location_info in ast.enumerate():
            site = tuple(ele(**self.assignments) for ele in location_info.position)
            self.sites.append(AHSCodegen.convert_position_to_SI_units(site))
            self.filling.append(location_info.filling.value)

        self.n_atoms = len(self.sites)

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
                site = AHSCodegen.convert_position_to_SI_units(tuple(location))
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

    def emit(self, nshots: int, analog_circuit: AnalogCircuit) -> AHSCodegenResult:
        self.visit(analog_circuit)

        return AHSCodegenResult(
            nshots=nshots,
            parallel_decoder=self.parallel_decoder,
            sites=self.sites,
            filling=self.filling,
            global_detuning=self.global_detuning,
            global_rabi_amplitude=self.global_rabi_amplitude,
            global_rabi_phase=self.global_rabi_phase,
            lattice_site_coefficients=self.lattice_site_coefficients,
            local_detuning=self.local_detuning,
        )
