from dataclasses import dataclass
from bloqade import start
from bloqade.analysis.common.assignment_scan import AssignmentScan
from bloqade.analysis.common.scan_channels import ScanChannels
from bloqade.analysis.common.scan_variables import ScanVariables
from bloqade.analysis.hardware.channels import ValidateChannels
from bloqade.analysis.hardware.piecewise_constant import (
    ValidatePiecewiseConstantChannel,
)
from bloqade.analysis.hardware.piecewise_linear import (
    ValidatePiecewiseLinearChannel,
)
from bloqade.codegen.hardware_v2.lattice import GenerateLattice, AHSLatticeData
from bloqade.codegen.hardware_v2.lattice_site_coefficients import (
    GenerateLatticeSiteCoefficients,
)
from bloqade.codegen.hardware_v2.piecewise_linear import (
    GeneratePiecewiseLinearChannel,
    PiecewiseLinear,
)
from bloqade.codegen.hardware_v2.piecewise_constant import (
    GeneratePiecewiseConstantChannel,
    PiecewiseConstant,
)
from bloqade.ir import analog_circuit
from bloqade.ir.control import pulse, sequence, field

from bloqade.rewrite.common.assign_variables import AssignBloqadeIR
from bloqade.rewrite.common.add_padding import AddPadding
from bloqade.rewrite.common.assign_to_literal import AssignToLiteral
from bloqade.rewrite.common.canonicalize import Canonicalizer
from bloqade.submission.capabilities import get_capabilities
from bloqade.submission.ir.braket import BraketTaskSpecification

from bloqade.submission.ir.parallel import ParallelDecoder

from beartype.typing import Optional, List, Tuple
from decimal import Decimal

from bloqade.submission.ir.task_specification import QuEraTaskSpecification


# Compiler passes


def analyze_channels(circuit):
    """1. Scan channels"""
    ValidateChannels().scan(circuit)
    level_couplings = ScanChannels().scan(circuit)

    # add missing channels
    fields = level_couplings[sequence.rydberg]

    updated_fields = {
        field_name: fields.get(field_name, {field.Uniform})
        for field_name in [pulse.detuning, pulse.rabi.amplitude, pulse.rabi.phase]
    }

    return {sequence.rydberg: updated_fields}


def add_padding(circuit, level_couplings):
    """2. Insert zero waveform in the explicit time intervals missing a waveform"""
    return AddPadding(level_couplings=level_couplings).visit(circuit)


def assign_program(circuit, assignments) -> sequence.SequenceExpr:
    """3. Assign variables, validate here"""

    final_assignments = AssignmentScan(assignments).emit(circuit)

    assigned_circuit = AssignBloqadeIR(final_assignments).visit(circuit)

    assigned_circuit = Canonicalizer().visit(assigned_circuit)

    assignment_analysis = ScanVariables().emit(circuit)

    if not assignment_analysis.is_assigned:
        missing_vars = assignment_analysis.scalar_vars + assignment_analysis.vector_vars
        raise ValueError(
            "Missing assignments for variables:\n"
            "\n".join(f"{var}" for var in missing_vars)
        )

    return assigned_circuit


def validate_waveforms(level_couplings, circuit) -> None:
    """4. validate piecewise linear and piecewise constant pieces of pulses"""
    channel_iter = (
        (level_coupling, field_name, sm)
        for level_coupling, fields in level_couplings.items()
        for field_name, spatial_modulations in fields.items()
        for sm in spatial_modulations
    )
    for channel in channel_iter:
        if channel[1] in [pulse.detuning, pulse.rabi.amplitude]:
            ValidatePiecewiseLinearChannel(*channel).visit(circuit)
        else:
            ValidatePiecewiseConstantChannel(*channel).visit(circuit)


def to_literal_and_canonicalize(circuit):
    """5. convert to literals and canonicalize"""
    circuit = AssignToLiteral().visit(circuit)
    return Canonicalizer().visit(circuit)


@dataclass
class AHSComponents:
    lattice_data: AHSLatticeData
    global_detuning: PiecewiseLinear
    global_amplitude: PiecewiseLinear
    global_phase: PiecewiseConstant
    local_detuning: Optional[PiecewiseLinear]
    lattice_site_coefficients: Optional[List[Decimal]]

    @staticmethod
    def convert_time_units(time: Decimal) -> Decimal:
        return time * Decimal("1e-6")

    @staticmethod
    def convert_energy_units(energy: Decimal) -> Decimal:
        return energy * Decimal("1e6")

    @staticmethod
    def convert_coordinate_units(
        length: Tuple[Decimal, Decimal]
    ) -> Tuple[Decimal, Decimal]:
        return (length[0] * Decimal("1e-6"), length[1] * Decimal("1e-6"))

    def generate_quera_ir(
        self, shots: int
    ) -> Tuple[QuEraTaskSpecification, Optional[ParallelDecoder]]:
        import bloqade.submission.ir.task_specification as task_spec

        lattice = task_spec.Lattice(
            sites=list(map(self.convert_coordinate_units, self.lattice_data.sites)),
            filling=self.lattice_data.filling,
        )

        global_detuning = task_spec.GlobalField(
            times=list(map(self.convert_time_units, self.global_detuning.times)),
            values=list(map(self.convert_energy_units, self.global_detuning.values)),
        )

        local_detuning = None

        if self.lattice_site_coefficients is not None:
            local_detuning = task_spec.LocalField(
                times=list(map(self.convert_time_units, self.local_detuning.times)),
                values=list(map(self.convert_energy_units, self.local_detuning.values)),
                lattice_site_coefficients=self.lattice_site_coefficients,
            )

        rabi_frequency_amplitude_field = task_spec.GlobalField(
            times=list(map(self.convert_time_units, self.global_amplitude.times)),
            values=list(map(self.convert_energy_units, self.global_amplitude.values)),
        )

        rabi_frequency_phase_field = task_spec.GlobalField(
            times=list(map(self.convert_time_units, self.global_phase.times)),
            values=self.global_phase.values,
        )

        detuning = task_spec.Detuning(
            global_=global_detuning,
            local=local_detuning,
        )

        rabi_frequency_amplitude = task_spec.RabiFrequencyAmplitude(
            global_=rabi_frequency_amplitude_field,
        )

        rabi_frequency_phase = task_spec.RabiFrequencyPhase(
            global_=rabi_frequency_phase_field,
        )

        rydberg = task_spec.RydbergHamiltonian(
            rabi_frequency_amplitude=rabi_frequency_amplitude,
            rabi_frequency_phase=rabi_frequency_phase,
            detuning=detuning,
        )

        effective_hamiltonian = task_spec.EffectiveHamiltonian(
            rydberg=rydberg,
        )

        return (
            task_spec.QuEraTaskSpecification(
                nshots=shots,
                lattice=lattice,
                effective_hamiltonian=effective_hamiltonian,
            ),
            self.lattice_data.parallel_decoder,
        )

    def generate_braket_ir(
        self, shots: int
    ) -> Tuple[BraketTaskSpecification, Optional[ParallelDecoder]]:
        import braket.ir.ahs as ahs
        from bloqade.submission.ir.braket import BraketTaskSpecification

        ahs_register = ahs.AtomArrangement(
            sites=list(map(self.convert_coordinate_units, self.lattice_data.sites)),
            filling=self.lattice_data.filling,
        )

        global_detuning_time_series = ahs.TimeSeries(
            times=list(map(self.convert_time_units, self.global_detuning.times)),
            values=list(map(self.convert_energy_units, self.global_detuning.values)),
        )

        local_detuning_time_series = None
        if self.lattice_site_coefficients is not None:
            local_detuning_time_series = ahs.TimeSeries(
                times=list(map(self.convert_time_units, self.local_detuning.times)),
                values=list(map(self.convert_energy_units, self.local_detuning.values)),
            )

        amplitude_time_series = ahs.TimeSeries(
            times=list(map(self.convert_time_units, self.global_amplitude.times)),
            values=list(map(self.convert_energy_units, self.global_amplitude.values)),
        )

        phase_time_series = ahs.TimeSeries(
            times=list(map(self.convert_time_units, self.global_phase.times)),
            values=self.global_phase.values,
        )

        detuning = ahs.PhysicalField(
            time_series=global_detuning_time_series,
            pattern="uniform",
        )

        amplitude = ahs.PhysicalField(
            time_series=amplitude_time_series,
            pattern="uniform",
        )

        phase = ahs.PhysicalField(
            time_series=phase_time_series,
            pattern="uniform",
        )

        local_detuning = None
        if self.lattice_site_coefficients is not None:
            local_detuning = ahs.PhysicalField(
                time_series=local_detuning_time_series,
                pattern=self.lattice_site_coefficients,
            )

        driving_field = ahs.DrivingField(
            detuning=detuning,
            amplitude=amplitude,
            phase=phase,
        )

        shiftingFields = []
        if self.lattice_site_coefficients is not None:
            shiftingFields = [ahs.ShiftingField(magnitude=local_detuning)]

        program = ahs.Program(
            setup=ahs.Setup(ahs_register=ahs_register),
            hamiltonian=ahs.Hamiltonian(
                drivingFields=[driving_field],
                shiftingFields=shiftingFields,
            ),
        )

        return (
            BraketTaskSpecification(nshots=shots, program=program),
            self.lattice_data.parallel_decoder,
        )


def generate_ahs_code(capabilities, level_couplings, final_circuit) -> AHSComponents:
    """6. generate ahs code"""

    ahs_lattice_data = GenerateLattice(capabilities).emit(final_circuit)

    global_detuning = GeneratePiecewiseLinearChannel(
        sequence.rydberg, pulse.detuning, field.Uniform
    ).visit(final_circuit)

    global_amplitude = GeneratePiecewiseLinearChannel(
        sequence.rydberg, pulse.rabi.amplitude, field.Uniform
    ).visit(final_circuit)

    global_phase = GeneratePiecewiseConstantChannel(
        sequence.rydberg, pulse.rabi.phase, field.Uniform
    ).visit(final_circuit)

    local_detuning = None
    lattice_site_coefficients = None

    extra_sm = level_couplings[sequence.rydberg][pulse.detuning] - {field.Uniform}

    if extra_sm:
        (sm,) = extra_sm

        lattice_site_coefficients = GenerateLatticeSiteCoefficients(
            sequence.rydberg, pulse.detuning, sm
        ).visit(final_circuit)

        local_detuning = GeneratePiecewiseLinearChannel(
            sequence.rydberg, pulse.detuning, sm
        ).visit(final_circuit)

    return AHSComponents(
        lattice_data=ahs_lattice_data,
        global_detuning=global_detuning,
        global_amplitude=global_amplitude,
        global_phase=global_phase,
        local_detuning=local_detuning,
        lattice_site_coefficients=lattice_site_coefficients,
    )


circuit = (
    start.rydberg.detuning.uniform.piecewise_linear([0.1, 1.2, 0.3], [-10, -10, 10, 10])
    .amplitude.uniform.piecewise_linear([0.1, 1.4, 0.1], [0, 10, 10, 0])
    .parse_circuit()
)

seq2 = start.rydberg.detuning.uniform.piecewise_linear(
    [0.3, 1.2, 0.3], [10, 10, -10, -10]
).parse_sequence()

circuit = analog_circuit.AnalogCircuit(circuit.register, circuit.sequence.append(seq2))

assignments = {}
capabilities = get_capabilities()


level_couplings = analyze_channels(circuit)
circuit = add_padding(circuit, level_couplings)
circuit = assign_program(circuit, assignments)
validate_waveforms(level_couplings, circuit)
circuit = to_literal_and_canonicalize(circuit)
ahs_code = generate_ahs_code(capabilities, level_couplings, circuit)
# 7. specialize to QuEra/Braket IR
quera_ir, parallel_decoder = ahs_code.generate_quera_ir(shots=100)
braket_ir, parallel_decoder = ahs_code.generate_braket_ir(shots=100)
print(quera_ir.effective_hamiltonian.rydberg.rabi_frequency_amplitude.global_)
