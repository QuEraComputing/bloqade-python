from bloqade.emulate.ir.atom_type import TwoLevelAtom
from bloqade.emulate.ir.emulator import (
    EmulatorProgram,
    Register,
    RabiOperatorData,
    RabiTerm,
    Fields,
    DetuningTerm,
    DetuningOperatorData,
    RabiOperatorType,
)
from bloqade.codegen.python.emulator_ir import (
    EmulatorProgramCodeGen,
    JITWaveform,
    LevelCoupling,
)
from bloqade import start
from bloqade.ir.control.sequence import rydberg
from bloqade.ir.control.pulse import detuning, rabi
from bloqade.ir.control.field import Location, RunTimeVector, ScaledLocations, Uniform
from decimal import Decimal

from bloqade.ir.scalar import cast


def test_codegen_global_detuning():
    program = (
        start.add_position((0, 0))
        .add_position((0, 5))
        .rydberg.detuning.uniform.piecewise_linear([0.1, 0.8, 0.1], [-10, -10, 10, 10])
        .parse_circuit()
    )

    detuning_waveform = (
        program.sequence.pulses[rydberg].fields[detuning].drives[Uniform]
    )

    compiled_waveform = JITWaveform({}, detuning_waveform, True)

    geometry = Register(
        TwoLevelAtom,
        [(Decimal("0"), Decimal("0")), (Decimal("0"), Decimal("5"))],
        Decimal("0"),
    )

    detuning_term = DetuningTerm(
        DetuningOperatorData({i: Decimal("1") for i in range(len(geometry))}),
        compiled_waveform,
    )

    rydberg_drive = Fields(detuning=[detuning_term], rabi=[])

    drives = {LevelCoupling.Rydberg: rydberg_drive}

    expected_emulator_ir = EmulatorProgram(
        register=geometry, duration=1.0, pulses=drives
    )

    emulator_ir = EmulatorProgramCodeGen().emit(program)

    print(emulator_ir)
    print(expected_emulator_ir)

    assert emulator_ir == expected_emulator_ir


def test_codegen_global_detuning_and_rabi():
    program = (
        start.add_position((0, 0))
        .add_position((0, 5))
        .rydberg.detuning.uniform.piecewise_linear([0.1, 0.8, 0.1], [-10, -10, 10, 10])
        .amplitude.uniform.piecewise_linear([0.1, 0.8, 0.1], [0, 10, 10, 0])
        .parse_circuit()
    )

    detuning_waveform = (
        program.sequence.pulses[rydberg].fields[detuning].drives[Uniform]
    )
    amplitude_waveform = (
        program.sequence.pulses[rydberg].fields[rabi.amplitude].drives[Uniform]
    )

    compiled_detuning = JITWaveform({}, detuning_waveform, True)
    compiled_amplitude = JITWaveform({}, amplitude_waveform, True)

    geometry = Register(
        TwoLevelAtom,
        [(Decimal("0"), Decimal("0")), (Decimal("0"), Decimal("5"))],
        Decimal("0"),
    )

    detuning_term = DetuningTerm(
        DetuningOperatorData({i: Decimal("1") for i in range(len(geometry))}),
        compiled_detuning,
    )

    rabi_term = RabiTerm(
        RabiOperatorData(
            RabiOperatorType.RabiSymmetric,
            {i: Decimal("1") for i in range(len(geometry))},
        ),
        compiled_amplitude,
        None,
    )

    rydberg_drive = Fields(detuning=[detuning_term], rabi=[rabi_term])

    drives = {LevelCoupling.Rydberg: rydberg_drive}

    expected_emulator_ir = EmulatorProgram(
        register=geometry, duration=1.0, pulses=drives
    )

    emulator_ir = EmulatorProgramCodeGen().emit(program)

    print(emulator_ir)
    print(expected_emulator_ir)

    assert emulator_ir == expected_emulator_ir


def test_codegen_detuning_max_terms():
    program = (
        start.add_position((0, 0))
        .add_position((0, 5))
        .rydberg.detuning.uniform.piecewise_linear([0.1, 0.8, 0.1], [-10, -10, 10, 10])
        .scale("mask_1")
        .piecewise_linear([0.1, 0.8, 0.1], [-20, -20, 10, 10])
        .location(0, 0.4)
        .piecewise_linear([0.1, 0.8, 0.1], [-10, -10, 20, 20])
        .parse_circuit()
    )
    mask_1_value = [0.5, 2.0]

    mask_1 = RunTimeVector("mask_1")
    location_0 = ScaledLocations({Location(0): cast(0.4)})
    uniform_wf = program.sequence.pulses[rydberg].fields[detuning].drives[Uniform]
    mask_1_wf = program.sequence.pulses[rydberg].fields[detuning].drives[mask_1]
    location_0_wf = program.sequence.pulses[rydberg].fields[detuning].drives[location_0]

    wf_0 = (1.0 * uniform_wf + mask_1_value[0] * mask_1_wf) + 0.4 * location_0_wf
    wf_1 = 1.0 * uniform_wf + mask_1_value[1] * mask_1_wf

    assignments = {"mask_1": mask_1_value}

    compiled_wf_0 = JITWaveform(assignments, wf_0, True)
    compiled_wf_1 = JITWaveform(assignments, wf_1, True)

    geometry = Register(
        TwoLevelAtom,
        [(Decimal("0"), Decimal("0")), (Decimal("0"), Decimal("5"))],
        Decimal("0"),
    )

    detuning_term_0 = DetuningTerm(
        DetuningOperatorData({0: Decimal("1")}),
        compiled_wf_0,
    )

    detuning_term_1 = DetuningTerm(
        DetuningOperatorData({1: Decimal("1")}),
        compiled_wf_1,
    )

    rydberg_drive = Fields(detuning=[detuning_term_0, detuning_term_1], rabi=[])
    drives = {LevelCoupling.Rydberg: rydberg_drive}

    expected_emulator_ir = EmulatorProgram(
        register=geometry, duration=1.0, pulses=drives
    )

    emulator_ir = EmulatorProgramCodeGen(assignments=assignments).emit(program)

    print(emulator_ir)
    print(expected_emulator_ir)

    assert emulator_ir == expected_emulator_ir


def test_codegen_rabi_max_terms():
    program = (
        start.add_position((0, 0))
        .add_position((0, 5))
        .rydberg.rabi.amplitude.uniform.piecewise_linear(
            [0.1, 0.8, 0.1], [-10, -10, 10, 10]
        )
        .scale("mask_1")
        .piecewise_linear([0.1, 0.8, 0.1], [-20, -20, 10, 10])
        .location(0, 0.4)
        .piecewise_linear([0.1, 0.8, 0.1], [-10, -10, 20, 20])
        .parse_circuit()
    )
    mask_1_value = [0.5, 2.0]

    mask_1 = RunTimeVector("mask_1")
    location_0 = ScaledLocations({Location(0): cast(0.4)})
    uniform_wf = program.sequence.pulses[rydberg].fields[rabi.amplitude].drives[Uniform]
    mask_1_wf = program.sequence.pulses[rydberg].fields[rabi.amplitude].drives[mask_1]
    location_0_wf = (
        program.sequence.pulses[rydberg].fields[rabi.amplitude].drives[location_0]
    )

    wf_0 = (1.0 * uniform_wf + mask_1_value[0] * mask_1_wf) + 0.4 * location_0_wf
    wf_1 = 1.0 * uniform_wf + mask_1_value[1] * mask_1_wf

    assignments = {"mask_1": mask_1_value}

    compiled_wf_0 = JITWaveform(assignments, wf_0, True)
    compiled_wf_1 = JITWaveform(assignments, wf_1, True)

    geometry = Register(
        TwoLevelAtom,
        [(Decimal("0"), Decimal("0")), (Decimal("0"), Decimal("5"))],
        Decimal("0"),
    )

    rabi_term_0 = RabiTerm(
        RabiOperatorData(
            RabiOperatorType.RabiSymmetric,
            {0: Decimal("1")},
        ),
        compiled_wf_0,
        None,
    )

    rabi_term_1 = RabiTerm(
        RabiOperatorData(
            RabiOperatorType.RabiSymmetric,
            {1: Decimal("1")},
        ),
        compiled_wf_1,
        None,
    )

    rydberg_drive = Fields(detuning=[], rabi=[rabi_term_0, rabi_term_1])

    drives = {LevelCoupling.Rydberg: rydberg_drive}

    expected_emulator_ir = EmulatorProgram(
        register=geometry, duration=1.0, pulses=drives
    )

    emulator_ir = EmulatorProgramCodeGen(assignments=assignments).emit(program)

    print(emulator_ir)
    print(expected_emulator_ir)

    assert emulator_ir == expected_emulator_ir


def test_codegen_rabi_uniform_phase():
    program = (
        start.add_position((0, 0))
        .add_position((0, 5))
        .rydberg.rabi.amplitude.uniform.piecewise_linear(
            [0.1, 0.8, 0.1], [-10, -10, 10, 10]
        )
        .rydberg.rabi.phase.uniform.piecewise_linear(
            [0.1, 0.8, 0.1], [-10, -10, 10, 10]
        )
        .parse_circuit()
    )

    uniform_amp = (
        program.sequence.pulses[rydberg].fields[rabi.amplitude].drives[Uniform]
    )
    uniform_phase = program.sequence.pulses[rydberg].fields[rabi.phase].drives[Uniform]

    assignments = {}

    compiled_amp = JITWaveform(assignments, uniform_amp, True)
    compiled_phase = JITWaveform(assignments, uniform_phase, True)

    geometry = Register(
        TwoLevelAtom,
        [(Decimal("0"), Decimal("0")), (Decimal("0"), Decimal("5"))],
        Decimal("0"),
    )

    rabi_term = RabiTerm(
        RabiOperatorData(
            RabiOperatorType.RabiAsymmetric,
            {i: Decimal("1") for i in range(len(geometry))},
        ),
        compiled_amp,
        compiled_phase,
    )

    rydberg_drive = Fields(detuning=[], rabi=[rabi_term])

    drives = {LevelCoupling.Rydberg: rydberg_drive}

    expected_emulator_ir = EmulatorProgram(
        register=geometry, duration=1.0, pulses=drives
    )

    emulator_ir = EmulatorProgramCodeGen(assignments=assignments).emit(program)

    print(emulator_ir)
    print(expected_emulator_ir)

    assert emulator_ir == expected_emulator_ir


def test_codegen_uniform_phase_rabi_max_terms():
    program = (
        start.add_position((0, 0))
        .add_position((0, 5))
        .rydberg.rabi.amplitude.uniform.piecewise_linear(
            [0.1, 0.8, 0.1], [-10, -10, 10, 10]
        )
        .scale("mask_1")
        .piecewise_linear([0.1, 0.8, 0.1], [-20, -20, 10, 10])
        .location(0, 0.4)
        .piecewise_linear([0.1, 0.8, 0.1], [-10, -10, 20, 20])
        .phase.uniform.piecewise_linear([0.1, 0.8, 0.1], [-10, -10, 10, 10])
        .parse_circuit()
    )

    mask_1_value = [0.5, 2.0]
    mask_1 = RunTimeVector("mask_1")
    location_0 = ScaledLocations({Location(0): cast(0.4)})

    uniform_amp = (
        program.sequence.pulses[rydberg].fields[rabi.amplitude].drives[Uniform]
    )
    mask_1_amp = program.sequence.pulses[rydberg].fields[rabi.amplitude].drives[mask_1]
    location_0_amp = (
        program.sequence.pulses[rydberg].fields[rabi.amplitude].drives[location_0]
    )
    phase_wf = program.sequence.pulses[rydberg].fields[rabi.phase].drives[Uniform]

    wf_0 = (1.0 * uniform_amp + mask_1_value[0] * mask_1_amp) + 0.4 * location_0_amp
    wf_1 = 1.0 * uniform_amp + mask_1_value[1] * mask_1_amp
    wf_0_phase = 1.0 * phase_wf
    wf_1_phase = 1.0 * phase_wf

    assignments = {"mask_1": mask_1_value}

    compiled_wf_0 = JITWaveform(assignments, wf_0, True)
    compiled_wf_1 = JITWaveform(assignments, wf_1, True)
    compiled_wf_0_phase = JITWaveform(assignments, wf_0_phase, True)
    compiled_wf_1_phase = JITWaveform(assignments, wf_1_phase, True)

    geometry = Register(
        TwoLevelAtom,
        [(Decimal("0"), Decimal("0")), (Decimal("0"), Decimal("5"))],
        Decimal("0"),
    )

    rabi_term_0 = RabiTerm(
        RabiOperatorData(
            RabiOperatorType.RabiAsymmetric,
            {0: Decimal("1")},
        ),
        compiled_wf_0,
        compiled_wf_0_phase,
    )

    rabi_term_1 = RabiTerm(
        RabiOperatorData(
            RabiOperatorType.RabiAsymmetric,
            {1: Decimal("1")},
        ),
        compiled_wf_1,
        compiled_wf_1_phase,
    )

    rydberg_drive = Fields(detuning=[], rabi=[rabi_term_0, rabi_term_1])

    drives = {LevelCoupling.Rydberg: rydberg_drive}

    expected_emulator_ir = EmulatorProgram(
        register=geometry, duration=1.0, pulses=drives
    )

    emulator_ir = EmulatorProgramCodeGen(assignments=assignments).emit(program)

    print(emulator_ir)
    print(expected_emulator_ir)

    assert emulator_ir == expected_emulator_ir


if __name__ == "__main__":
    test_codegen_uniform_phase_rabi_max_terms()
