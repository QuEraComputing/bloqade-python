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
from bloqade.emulate.codegen.emulator_ir import (
    EmulatorProgramCodeGen,
    CompiledWaveform,
    LevelCoupling,
)
from bloqade import start
from bloqade.ir.control.sequence import rydberg
from bloqade.ir.control.pulse import detuning, rabi
from bloqade.ir.control.field import Uniform
from decimal import Decimal


def test_codegen_detuning():
    program = (
        start.add_position((0, 0))
        .add_position((0, 5))
        .rydberg.detuning.uniform.piecewise_linear([0.1, 0.8, 0.1], [-10, -10, 10, 10])
        .parse_circuit()
    )

    detuning_waveform = program.sequence.pulses[rydberg].fields[detuning].value[Uniform]

    compiled_waveform = CompiledWaveform({}, detuning_waveform)

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


def test_codegen_detuning_and_rabi():
    program = (
        start.add_position((0, 0))
        .add_position((0, 5))
        .rydberg.detuning.uniform.piecewise_linear([0.1, 0.8, 0.1], [-10, -10, 10, 10])
        .amplitude.uniform.piecewise_linear([0.1, 0.8, 0.1], [0, 10, 10, 0])
        .parse_circuit()
    )

    detuning_waveform = program.sequence.pulses[rydberg].fields[detuning].value[Uniform]
    amplitude_waveform = (
        program.sequence.pulses[rydberg].fields[rabi.amplitude].value[Uniform]
    )

    compiled_detuning = CompiledWaveform({}, detuning_waveform)
    compiled_amplitude = CompiledWaveform({}, amplitude_waveform)

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
