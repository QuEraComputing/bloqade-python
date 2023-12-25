from decimal import Decimal
import pytest
from bloqade.compiler.analysis.hardware.piecewise_linear import (
    ValidatePiecewiseLinearChannel,
)
from bloqade.compiler.analysis.hardware.piecewise_constant import (
    ValidatePiecewiseConstantChannel,
)
from bloqade.compiler.analysis.hardware.channels import ValidateChannels
from bloqade.ir import analog_circuit
from bloqade.compiler.rewrite.common.add_padding import AddPadding

import bloqade.ir.control.sequence as sequence
import bloqade.ir.control.pulse as pulse
import bloqade.ir.control.field as field
import bloqade.ir.control.waveform as waveform

from bloqade import piecewise_constant, piecewise_linear, var, start


@waveform.to_waveform(1)
def py_func(x):
    return x


def test_validate_channels_happy_path():
    wf1 = waveform.Constant(1, 1)
    wf2 = waveform.Linear(1, 1, 1)

    sm = field.AssignedRunTimeVector("mask", [Decimal("1.0"), Decimal("2.0")])

    f1 = field.Field({field.Uniform: wf1, sm: wf2})
    f2 = field.Field({sm: wf2})
    f3 = f1.add(f2)

    p1 = pulse.Pulse({pulse.detuning: f1})
    p2 = pulse.Pulse({pulse.detuning: f2})
    p3 = pulse.Pulse({pulse.detuning: f3})

    s1 = sequence.Sequence({sequence.rydberg: p1})
    s2 = sequence.Sequence({sequence.rydberg: p2})
    s3 = sequence.Sequence({sequence.rydberg: p3})

    register = start.add_position([(0, 0), (1, 1)])
    circuit1 = analog_circuit.AnalogCircuit(register, s1)
    circuit2 = analog_circuit.AnalogCircuit(register, s2)
    circuit3 = analog_circuit.AnalogCircuit(register, s3)

    assert ValidateChannels().scan(circuit1) is None
    assert ValidateChannels().scan(circuit2) is None
    assert ValidateChannels().scan(circuit3) is None


def test_validate_channels_sad_path():
    wf1 = waveform.Constant(1, 1)
    wf2 = waveform.Linear(1, 1, 1)
    wf3 = waveform.Poly([1, 2], 1)

    sm1 = field.AssignedRunTimeVector(
        "mask", [Decimal("1.0"), Decimal("2.0"), Decimal("3.0")]
    )
    sm2 = field.ScaledLocations.create({0: Decimal("1.0"), 1: Decimal("2.0")})
    sm2_broken = field.ScaledLocations.create({1: Decimal("1.0"), 3: Decimal("2.0")})
    sm1_broken = field.AssignedRunTimeVector("mask", [Decimal("1.9"), Decimal("1.0")])

    f0 = field.Field({field.Uniform: wf1, sm1: wf2})
    f1 = field.Field({field.Uniform: wf1, sm1: wf2, sm2: wf3})
    f2 = field.Field({field.Uniform: wf1, sm2_broken: wf2})
    f3 = field.Field({field.Uniform: wf1, sm1_broken: wf2})

    p0 = pulse.Pulse({pulse.detuning: f0})
    p1 = pulse.Pulse({pulse.detuning: f1})
    p2 = pulse.Pulse({pulse.detuning: f2})
    p3 = pulse.Pulse({pulse.detuning: f3})
    p4 = pulse.Pulse({pulse.rabi.amplitude: f1, pulse.detuning: f0})

    s1 = sequence.Sequence({sequence.rydberg: p1})
    s2 = sequence.Sequence({sequence.rydberg: p2})
    s3 = sequence.Sequence({sequence.rydberg: p3})
    s4 = sequence.Sequence({sequence.hyperfine: p0, sequence.rydberg: p0})
    s5 = sequence.Sequence({sequence.rydberg: p4})

    register = start.add_position([(0, 0), (1, 1), (2, 2)])
    circuit1 = analog_circuit.AnalogCircuit(register, s1)
    circuit2 = analog_circuit.AnalogCircuit(register, s2)
    circuit3 = analog_circuit.AnalogCircuit(register, s3)
    circuit4 = analog_circuit.AnalogCircuit(register, s4)
    circuit5 = analog_circuit.AnalogCircuit(register, s5)

    with pytest.raises(ValueError):
        ValidateChannels().scan(circuit1)

    with pytest.raises(ValueError):
        ValidateChannels().scan(circuit2)

    with pytest.raises(ValueError):
        ValidateChannels().scan(circuit3)

    with pytest.raises(ValueError):
        ValidateChannels().scan(circuit4)

    with pytest.raises(ValueError):
        ValidateChannels().scan(circuit5)


def test_piecewise_constant_waveform_happy_path():
    validator = ValidatePiecewiseConstantChannel(
        level_coupling=sequence.rydberg,
        field_name=pulse.rabi.amplitude,
        spatial_modulations=field.Uniform,
    )

    wf1 = waveform.Constant(1, 1)
    wf2 = waveform.Linear(1, 1, 1)
    wf3 = waveform.Poly([], 1)
    wf4 = waveform.Poly([1], 1)
    wf5 = py_func.sample(0.1, "constant")

    assert validator.scan(wf1) is None
    assert validator.scan(wf2) is None
    assert validator.scan(wf3) is None
    assert validator.scan(wf4) is None
    assert validator.scan(wf5) is None
    assert validator.scan(wf1.append(wf2).append(wf3)) is None


def test_piecewise_constant_waveform_sad_path():
    validator = ValidatePiecewiseConstantChannel(
        level_coupling=sequence.rydberg,
        field_name=pulse.rabi.amplitude,
        spatial_modulations=field.Uniform,
    )

    wf0 = piecewise_constant([1, 2, 3], [1, 2, 3])

    wf1 = waveform.Linear(1, 2, 1)
    wf2 = waveform.Poly([1, 2, 3], 1)
    wf3 = py_func.sample(0.1, "linear")
    wf4 = py_func
    wf5 = wf2.smooth(1, "Gaussian")
    wf6 = wf0.append(wf1)

    with pytest.raises(ValueError):
        validator.scan(wf1)

    with pytest.raises(ValueError):
        validator.scan(wf2)

    with pytest.raises(ValueError):
        validator.scan(wf3)

    with pytest.raises(ValueError):
        validator.scan(wf4)

    with pytest.raises(ValueError):
        validator.scan(wf5)

    with pytest.raises(ValueError):
        validator.scan(wf6)


def test_piecewise_linear_waveform_happy_path():
    validator = ValidatePiecewiseLinearChannel(
        level_coupling=sequence.rydberg,
        field_name=pulse.rabi.amplitude,
        spatial_modulations=field.Uniform,
    )

    wf1 = waveform.Constant(1, 1)
    wf2 = waveform.Linear(1, 2, 1)
    wf3 = waveform.Poly([], 1)
    wf4 = waveform.Poly([1], 1)
    wf5 = waveform.Poly([1, 2], 1)
    wf6 = py_func.sample(0.1, "linear")
    wf7 = piecewise_linear([0.1, 0.2, 0.3], [1, 2, 3, 4])
    wf8 = wf7[0.05:0.25]
    wf9 = wf1 + wf2

    assert validator.scan(wf1) is None
    assert validator.scan(wf2) is None
    assert validator.scan(wf3) is None
    assert validator.scan(wf4) is None
    assert validator.scan(wf5) is None
    assert validator.scan(wf6) is None
    assert validator.scan(wf7) is None
    assert validator.scan(wf8) is None
    assert validator.scan(wf9) is None


def test_piecewise_linear_waveform_sad_path():
    validator = ValidatePiecewiseLinearChannel(
        level_coupling=sequence.rydberg,
        field_name=pulse.rabi.amplitude,
        spatial_modulations=field.Uniform,
    )

    wf1 = py_func
    wf2 = py_func.sample(0.1, "constant")
    wf3 = waveform.Poly([1, 2, 3], 1)
    wf4 = py_func.smooth(1, "Gaussian")
    wf5 = AddPadding().visit(waveform.Linear(1, 2, 0.5) + waveform.Linear(2, 3, 1))
    wf6 = waveform.Linear(1, 2, 0.5).append(waveform.Linear(2.1, 3, 1))

    with pytest.raises(ValueError):
        validator.scan(wf1)

    with pytest.raises(ValueError):
        validator.scan(wf2)

    with pytest.raises(ValueError):
        validator.scan(wf3)

    with pytest.raises(ValueError):
        validator.scan(wf4)

    with pytest.raises(ValueError):
        validator.scan(wf5)

    with pytest.raises(ValueError):
        validator.scan(wf6)


def test_pulse_happy_path():
    linear = ValidatePiecewiseLinearChannel(
        level_coupling=sequence.rydberg,
        field_name=pulse.rabi.amplitude,
        spatial_modulations=field.Uniform,
    )
    constant = ValidatePiecewiseConstantChannel(
        level_coupling=sequence.rydberg,
        field_name=pulse.rabi.amplitude,
        spatial_modulations=field.Uniform,
    )

    p1 = pulse.Pulse(
        {pulse.rabi.amplitude: field.Field({field.Uniform: waveform.Constant(1, 1)})}
    )
    p2 = pulse.Pulse(
        {pulse.rabi.amplitude: field.Field({field.Uniform: waveform.Linear(1, 0, 1)})}
    )
    p3 = pulse.Pulse(
        {
            pulse.rabi.amplitude: field.Field(
                {field.Uniform: py_func.sample(0.1, "constant")}
            )
        }
    )

    p_test = pulse.NamedPulse("test", (p1.append(p2))[: var("t")])
    assert linear.scan(p_test) is None
    assert constant.scan(p3) is None


def test_pulse_sad_path():
    linear = ValidatePiecewiseLinearChannel(
        level_coupling=sequence.rydberg,
        field_name=pulse.rabi.amplitude,
        spatial_modulations=field.Uniform,
    )
    constant = ValidatePiecewiseConstantChannel(
        level_coupling=sequence.rydberg,
        field_name=pulse.rabi.amplitude,
        spatial_modulations=field.Uniform,
    )

    p1 = pulse.Pulse(
        {pulse.rabi.amplitude: field.Field({field.Uniform: waveform.Constant(1, 1)})}
    )
    p2 = pulse.Pulse(
        {pulse.rabi.amplitude: field.Field({field.Uniform: waveform.Linear(1, 0, 1)})}
    )
    p3 = pulse.Pulse({pulse.rabi.amplitude: field.Field({field.Uniform: py_func})})
    p4 = pulse.Pulse(
        {
            pulse.rabi.amplitude: field.Field(
                {field.Uniform: py_func.sample(0.1, "linear")}
            )
        }
    )

    p1_test = p1.append(p2).append(p3)

    with pytest.raises(ValueError):
        linear.scan(p1_test)

    with pytest.raises(ValueError):
        constant.scan(p4)


def test_sequence_happy_path():
    linear = ValidatePiecewiseLinearChannel(
        level_coupling=sequence.rydberg,
        field_name=pulse.rabi.amplitude,
        spatial_modulations=field.Uniform,
    )
    constant = ValidatePiecewiseConstantChannel(
        level_coupling=sequence.rydberg,
        field_name=pulse.rabi.amplitude,
        spatial_modulations=field.Uniform,
    )

    s1 = sequence.Sequence(
        {
            sequence.rydberg: pulse.Pulse(
                {
                    pulse.rabi.amplitude: field.Field(
                        {field.Uniform: waveform.Constant(1, 1)}
                    )
                }
            )
        }
    )
    s2 = sequence.Sequence(
        {
            sequence.rydberg: pulse.Pulse(
                {
                    pulse.rabi.amplitude: field.Field(
                        {field.Uniform: waveform.Linear(1, 0, 1)}
                    )
                }
            )
        }
    )
    s3 = sequence.Sequence(
        {
            sequence.rydberg: pulse.Pulse(
                {
                    pulse.rabi.amplitude: field.Field(
                        {field.Uniform: py_func.sample(0.1, "constant")}
                    )
                }
            )
        }
    )

    p_test = sequence.NamedSequence(name="test", sequence=(s1.append(s2))[: var("t")])
    assert linear.scan(p_test) is None
    assert constant.scan(s3) is None


def test_sequence_sad_path():
    linear = ValidatePiecewiseLinearChannel(
        level_coupling=sequence.rydberg,
        field_name=pulse.rabi.amplitude,
        spatial_modulations=field.Uniform,
    )
    constant = ValidatePiecewiseConstantChannel(
        level_coupling=sequence.rydberg,
        field_name=pulse.rabi.amplitude,
        spatial_modulations=field.Uniform,
    )

    p1 = sequence.Sequence(
        {
            sequence.rydberg: pulse.Pulse(
                {
                    pulse.rabi.amplitude: field.Field(
                        {field.Uniform: waveform.Constant(1, 1)}
                    )
                }
            )
        }
    )
    p2 = sequence.Sequence(
        {
            sequence.rydberg: pulse.Pulse(
                {
                    pulse.rabi.amplitude: field.Field(
                        {field.Uniform: waveform.Linear(1, 0, 1)}
                    )
                }
            )
        }
    )
    p3 = sequence.Sequence(
        {
            sequence.rydberg: pulse.Pulse(
                {pulse.rabi.amplitude: field.Field({field.Uniform: py_func})}
            )
        }
    )
    p4 = sequence.Sequence(
        {
            sequence.rydberg: pulse.Pulse(
                {
                    pulse.rabi.amplitude: field.Field(
                        {field.Uniform: py_func.sample(0.1, "linear")}
                    )
                }
            )
        }
    )

    p1_test = p1.append(p2).append(p3)

    with pytest.raises(ValueError):
        linear.scan(p1_test)

    with pytest.raises(ValueError):
        constant.scan(p4)
