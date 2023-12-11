from bloqade.builder.typing import ParamType

from bloqade.compiler.hardware.components import AHSComponents
from bloqade.ir import analog_circuit
from bloqade.ir.control import pulse, sequence, field

from bloqade.submission.ir.braket import BraketTaskSpecification

from bloqade.submission.ir.capabilities import QuEraCapabilities
from bloqade.submission.ir.task_specification import QuEraTaskSpecification

from beartype.typing import Dict, Optional


def analyze_channels(circuit: analog_circuit.AnalogCircuit) -> Dict:
    """1. Scan channels

    This pass checks to make sure that:
    * There is no hyperfine coupling in the sequence
    * There are no non-uniform spatial modulation for rabi phase and amplitude
    * there is no more than one non-uniform spatial modulation for detuning

    Args:
        circuit: AnalogCircuit to analyze

    Returns:
        level_couplings: Dictionary containing the required channels for the
            sequence. Note that this will insert a uniform field for any missing
            channels.

    Raises:
        ValueError: If there is hyperfine coupling in the sequence.
        ValueError: If there is more than one non-uniform spatial modulation for
            detuning.
        ValueError: If there are non-uniform spatial modulations for rabi phase
            and amplitude.

    """
    from bloqade.analysis.hardware.channels import ValidateChannels
    from bloqade.analysis.common.scan_channels import ScanChannels

    ValidateChannels().scan(circuit)
    level_couplings = ScanChannels().scan(circuit)

    # add missing channels
    fields = level_couplings[sequence.rydberg]
    # detuning, phase and amplitude are required
    # to have at least a uniform field
    updated_fields = {
        field_name: fields.get(field_name, {field.Uniform})
        for field_name in [pulse.detuning, pulse.rabi.amplitude, pulse.rabi.phase]
    }

    return {sequence.rydberg: updated_fields}


def add_padding(
    circuit: analog_circuit.AnalogCircuit, level_couplings: Dict
) -> analog_circuit.AnalogCircuit:
    """2. Insert zero waveform in the explicit time intervals missing a waveform

    This pass inserts a zero waveform in the explicit time intervals missing a
    waveform. This is required for later analysis passes to check that the
    waveforms are compatible with the hardware.

    Args:
        circuit: AnalogCircuit to add padding to
        level_couplings: Dictionary containing the given channels for the
            sequence.

    Return
        circuit: AnalogCircuit with zero waveforms inserted in the explicit time
            intervals missing a waveform.

    """
    from bloqade.rewrite.common.add_padding import AddPadding

    return AddPadding(level_couplings=level_couplings).visit(circuit)


def assign_circuit(
    circuit: analog_circuit.AnalogCircuit, assignments: Dict[str, ParamType]
) -> analog_circuit.AnalogCircuit:
    """3. Assign variables and validate assignment

    This pass assigns variables to the circuit and validates that all variables
    have been assigned.

    Args:
        circuit: AnalogCircuit to assign variables to
        assignments: Dictionary containing the assignments for the variables in
            the circuit.

    Returns:
        assigned_circuit: AnalogCircuit with variables assigned.

    Raises:
        ValueError: If there are any variables that have not been assigned.

    """
    from bloqade.analysis.common.assignment_scan import AssignmentScan
    from bloqade.analysis.common.scan_variables import ScanVariables
    from bloqade.rewrite.common.assign_variables import AssignBloqadeIR

    final_assignments = AssignmentScan(assignments).emit(circuit)

    assigned_circuit = AssignBloqadeIR(final_assignments).visit(circuit)

    assignment_analysis = ScanVariables().emit(circuit)

    if not assignment_analysis.is_assigned:
        missing_vars = assignment_analysis.scalar_vars + assignment_analysis.vector_vars
        raise ValueError(
            "Missing assignments for variables:\n"
            "\n".join(f"{var}" for var in missing_vars)
        )

    return assigned_circuit


def validate_waveforms(
    circuit: analog_circuit.AnalogCircuit, level_couplings: Dict
) -> None:
    """4. validate piecewise linear and piecewise constant pieces of pulses

    This pass check to make sure that the waveforms are compatible with the
    hardware. This includes checking that the waveforms are piecewise linear or
    piecewise constant. It also checks that the waveforms are compatible with
    the given channels.

    Args:
        circuit: AnalogCircuit to validate waveforms for
        level_couplings: Dictionary containing the given channels for the
            sequence.

    Raises:
        ValueError: If the waveforms are not piecewise linear or piecewise
            constant, e.g. the waveform is not continuous.
        ValueError: If a waveform segment is not compatible with the given
            channels.

    """
    from bloqade.analysis.hardware.piecewise_constant import (
        ValidatePiecewiseConstantChannel,
    )
    from bloqade.analysis.hardware.piecewise_linear import (
        ValidatePiecewiseLinearChannel,
    )

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


def to_literal_and_canonicalize(
    circuit: analog_circuit.AnalogCircuit,
) -> analog_circuit.AnalogCircuit:
    """5. convert to literals and canonicalize

    This pass converts all assgined variables to literals and canonicalizes the
    circuit. This should simplify the circuit and make it faster to compile.

    Args:
        circuit: AnalogCircuit to convert to literals and canonicalize.

    Returns:
        circuit: AnalogCircuit with all literals and canonicalized.

    """
    from bloqade.rewrite.common.assign_to_literal import AssignToLiteral
    from bloqade.rewrite.common.canonicalize import Canonicalizer

    return Canonicalizer().visit(AssignToLiteral().visit(circuit))


def generate_ahs_code(
    capabilities: Optional[QuEraCapabilities],
    level_couplings: Dict,
    circuit: analog_circuit.AnalogCircuit,
) -> AHSComponents:
    """6. generate ahs code

    Generates the AHS code for the given circuit. This includes generating the
    lattice data, global detuning, global amplitude, global phase, local
    detuning and lattice site coefficients (if applicable).

    Args:
        capabilities (QuEraCapabilities | None): Capabilities of the hardware.
        level_couplings (Dict): Dictionary containing the given channels for the
            sequence.
        circuit (AnalogCircuit): AnalogCircuit to generate AHS code for.

    Returns:
        ahs_components (AHSComponents): A collection of the AHS components
            generated for the given circuit. Can be used to generate the QuEra
            and Braket IR.

    Raises:
        ValueError: If the capabilities are not provided but the circuit has
            a ParallelRegister. This is because the ParallelRegister requires
            the capabilities to generate the lattice data.

    """
    from bloqade.codegen.hardware_v2.lattice import GenerateLattice
    from bloqade.codegen.hardware_v2.lattice_site_coefficients import (
        GenerateLatticeSiteCoefficients,
    )
    from bloqade.codegen.hardware_v2.piecewise_linear import (
        GeneratePiecewiseLinearChannel,
    )
    from bloqade.codegen.hardware_v2.piecewise_constant import (
        GeneratePiecewiseConstantChannel,
    )

    ahs_lattice_data = GenerateLattice(capabilities).emit(circuit)

    global_detuning = GeneratePiecewiseLinearChannel(
        sequence.rydberg, pulse.detuning, field.Uniform
    ).visit(circuit)

    global_amplitude = GeneratePiecewiseLinearChannel(
        sequence.rydberg, pulse.rabi.amplitude, field.Uniform
    ).visit(circuit)

    global_phase = GeneratePiecewiseConstantChannel(
        sequence.rydberg, pulse.rabi.phase, field.Uniform
    ).visit(circuit)

    local_detuning = None
    lattice_site_coefficients = None

    extra_sm = level_couplings[sequence.rydberg][pulse.detuning] - {field.Uniform}

    if extra_sm:
        (sm,) = extra_sm

        lattice_site_coefficients = GenerateLatticeSiteCoefficients(
            parallel_decoder=ahs_lattice_data.parallel_decoder
        ).visit(circuit)

        local_detuning = GeneratePiecewiseLinearChannel(
            sequence.rydberg, pulse.detuning, sm
        ).visit(circuit)

    return AHSComponents(
        lattice_data=ahs_lattice_data,
        global_detuning=global_detuning,
        global_amplitude=global_amplitude,
        global_phase=global_phase,
        local_detuning=local_detuning,
        lattice_site_coefficients=lattice_site_coefficients,
    )


def generate_quera_ir(
    ahs_components: AHSComponents, shots: int
) -> QuEraTaskSpecification:
    """7. generate quera ir

    This pass takes the AHS components and generates the QuEra IR.

    Args:
        ahs_components (AHSComponents): A collection of the AHS components
            generated for the given circuit.
        shots (int): Number of shots to run the circuit for.

    Returns:
        task_specification (QuEraTaskSpecification): QuEra IR for the given
            circuit.

    """
    import bloqade.submission.ir.task_specification as task_spec
    from bloqade.compiler.hardware.units import (
        convert_time_units,
        convert_energy_units,
        convert_coordinate_units,
    )

    lattice = task_spec.Lattice(
        sites=list(
            map(
                convert_coordinate_units,
                ahs_components.lattice_data.sites,
            )
        ),
        filling=ahs_components.lattice_data.filling,
    )

    global_detuning = task_spec.GlobalField(
        times=list(map(convert_time_units, ahs_components.global_detuning.times)),
        values=list(map(convert_energy_units, ahs_components.global_detuning.values)),
    )

    local_detuning = None

    if ahs_components.lattice_site_coefficients is not None:
        local_detuning = task_spec.LocalField(
            times=list(map(convert_time_units, ahs_components.local_detuning.times)),
            values=list(
                map(convert_energy_units, ahs_components.local_detuning.values)
            ),
            lattice_site_coefficients=ahs_components.lattice_site_coefficients,
        )

    rabi_frequency_amplitude_field = task_spec.GlobalField(
        times=list(map(convert_time_units, ahs_components.global_amplitude.times)),
        values=list(map(convert_energy_units, ahs_components.global_amplitude.values)),
    )

    rabi_frequency_phase_field = task_spec.GlobalField(
        times=list(map(convert_time_units, ahs_components.global_phase.times)),
        values=ahs_components.global_phase.values,
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

    return task_spec.QuEraTaskSpecification(
        nshots=shots,
        lattice=lattice,
        effective_hamiltonian=effective_hamiltonian,
    )


def generate_braket_ir(
    ahs_components: AHSComponents, shots: int
) -> BraketTaskSpecification:
    """7. generate braket ir

    This pass takes the AHS components and generates the Braket IR.

    Args:
        ahs_components (AHSComponents): A collection of the AHS components
            generated for the given circuit.
        shots (int): Number of shots to run the circuit for.

    Returns:
        task_specification (BraketTaskSpecification): Braket IR for the given
            circuit.

    """
    import braket.ir.ahs as ahs
    from bloqade.compiler.hardware.units import (
        convert_time_units,
        convert_energy_units,
        convert_coordinate_units,
    )

    ahs_register = ahs.AtomArrangement(
        sites=list(map(convert_coordinate_units, ahs_components.lattice_data.sites)),
        filling=ahs_components.lattice_data.filling,
    )

    global_detuning_time_series = ahs.TimeSeries(
        times=list(map(convert_time_units, ahs_components.global_detuning.times)),
        values=list(map(convert_energy_units, ahs_components.global_detuning.values)),
    )

    local_detuning_time_series = None
    if ahs_components.lattice_site_coefficients is not None:
        local_detuning_time_series = ahs.TimeSeries(
            times=list(map(convert_time_units, ahs_components.local_detuning.times)),
            values=list(
                map(convert_energy_units, ahs_components.local_detuning.values)
            ),
        )

    amplitude_time_series = ahs.TimeSeries(
        times=list(map(convert_time_units, ahs_components.global_amplitude.times)),
        values=list(map(convert_energy_units, ahs_components.global_amplitude.values)),
    )

    phase_time_series = ahs.TimeSeries(
        times=list(map(convert_time_units, ahs_components.global_phase.times)),
        values=ahs_components.global_phase.values,
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
    if ahs_components.lattice_site_coefficients is not None:
        local_detuning = ahs.PhysicalField(
            time_series=local_detuning_time_series,
            pattern=ahs_components.lattice_site_coefficients,
        )

    driving_field = ahs.DrivingField(
        detuning=detuning,
        amplitude=amplitude,
        phase=phase,
    )

    shiftingFields = []
    if ahs_components.lattice_site_coefficients is not None:
        shiftingFields = [ahs.ShiftingField(magnitude=local_detuning)]

    program = ahs.Program(
        setup=ahs.Setup(ahs_register=ahs_register),
        hamiltonian=ahs.Hamiltonian(
            drivingFields=[driving_field],
            shiftingFields=shiftingFields,
        ),
    )

    return BraketTaskSpecification(nshots=shots, program=program)
