import pytest
from bloqade.ir.control import waveform, field, pulse, sequence
from bloqade.ir import analog_circuit
from bloqade.codegen.hardware_v2.piecewise_linear import (
    PiecewiseLinear,
    GeneratePiecewiseLinearChannel,
)
from bloqade.codegen.hardware_v2.piecewise_constant import (
    PiecewiseConstant,
    GeneratePiecewiseConstantChannel,
)
from bloqade import piecewise_linear, piecewise_constant, start
import numpy as np
from decimal import Decimal


@waveform.to_waveform(4.0)
def wf(t):
    return np.sin(t)


def test_error_pwl():
    with pytest.raises(TypeError):
        GeneratePiecewiseLinearChannel(
            sequence.rydberg, pulse.detuning, field.Uniform
        ).visit(wf)


def test_error_pwc():
    with pytest.raises(TypeError):
        GeneratePiecewiseConstantChannel(
            sequence.rydberg, pulse.detuning, field.Uniform
        ).visit(wf)


def test_waveform_append_pwl():
    visitor = GeneratePiecewiseLinearChannel(
        sequence.rydberg, pulse.detuning, field.Uniform
    )

    wf = piecewise_linear(
        durations=[1, 2, 3],
        values=[0, 1, 0, 1],
    )

    expected = PiecewiseLinear(
        times=[Decimal("0"), Decimal("1"), Decimal("3"), Decimal("6")],
        values=[Decimal("0"), Decimal("1"), Decimal("0"), Decimal("1")],
    )
    assert visitor.visit(wf) == expected

    new_wf = wf.append(waveform.Poly([1, 3], 2)).append(waveform.Constant(7, 0.5))

    expected = PiecewiseLinear(
        times=[
            Decimal("0"),
            Decimal("1"),
            Decimal("3"),
            Decimal("6"),
            Decimal("8"),
            Decimal("8.5"),
        ],
        values=[
            Decimal("0"),
            Decimal("1"),
            Decimal("0"),
            Decimal("1"),
            Decimal("7"),
            Decimal("7"),
        ],
    )

    assert visitor.visit(new_wf) == expected


def test_waveform_append_pwc():
    visitor = GeneratePiecewiseConstantChannel(
        sequence.rydberg, pulse.detuning, field.Uniform
    )

    wf1 = piecewise_constant(
        durations=[1, 2, 3],
        values=[1, 2, 3],
    )

    expected = PiecewiseConstant(
        [Decimal("0"), Decimal("1"), Decimal("3"), Decimal("6")],
        [Decimal("1"), Decimal("2"), Decimal("3"), Decimal("3")],
    )

    assert visitor.visit(wf1) == expected

    wf2 = wf1.append(waveform.Linear(5, 5, 1)).append(waveform.Poly([1], 4))

    expected = PiecewiseConstant(
        [
            Decimal("0"),
            Decimal("1"),
            Decimal("3"),
            Decimal("6"),
            Decimal("7"),
            Decimal("11"),
        ],
        [
            Decimal("1"),
            Decimal("2"),
            Decimal("3"),
            Decimal("5"),
            Decimal("1"),
            Decimal("1"),
        ],
    )

    assert visitor.visit(wf2) == expected


def test_waveform_sample_pwl():
    visitor = GeneratePiecewiseLinearChannel(
        sequence.rydberg, pulse.detuning, field.Uniform
    )

    pwl_wf = wf.sample(0.1, waveform.Interpolation.Linear)

    times, values = pwl_wf.samples()

    expected = PiecewiseLinear(times=times, values=values)

    assert visitor.visit(pwl_wf) == expected


def test_waveform_sample_pwc():
    visitor = GeneratePiecewiseConstantChannel(
        sequence.rydberg, pulse.detuning, field.Uniform
    )

    pwl_wf = wf.sample(0.1, waveform.Interpolation.Constant)

    times, values = pwl_wf.samples()

    expected = PiecewiseConstant(times=times, values=values)

    assert visitor.visit(pwl_wf) == expected


def test_waveform_add_pwl():
    left = waveform.Linear(0, 1, 2)
    right = piecewise_linear([1, 1], [0, 1, 0])
    wf = left + right

    visitor = GeneratePiecewiseLinearChannel(
        sequence.rydberg, pulse.detuning, field.Uniform
    )

    expected = PiecewiseLinear(
        times=[Decimal("0"), Decimal("1"), Decimal("2")],
        values=[Decimal("0"), Decimal("1.5"), Decimal("1.0")],
    )

    assert visitor.visit(wf) == expected


def test_waveform_add_pwc():
    left = piecewise_constant([0.5, 1.5], [1, 0])
    right = piecewise_constant([1, 1], [0, 1])
    wf = left + right

    visitor = GeneratePiecewiseConstantChannel(
        sequence.rydberg, pulse.detuning, field.Uniform
    )

    expected = PiecewiseConstant(
        times=[Decimal("0.0"), Decimal("0.5"), Decimal("1.0"), Decimal("2")],
        values=[Decimal("1.0"), Decimal("0.0"), Decimal("1.0"), Decimal("1.0")],
    )

    assert visitor.visit(wf) == expected

    left = piecewise_constant([1, 1], [1, 0])
    right = piecewise_constant([1, 1], [0, 1])
    wf = left + right

    expected = PiecewiseConstant(
        times=[Decimal("0.0"), Decimal("1.0"), Decimal("2")],
        values=[Decimal("1.0"), Decimal("1.0"), Decimal("1.0")],
    )

    assert visitor.visit(wf) == expected


def test_waveform_slice_pwl():
    wf1 = waveform.Linear(0, 1, 2)[0.5:1.5]

    visitor = GeneratePiecewiseLinearChannel(
        sequence.rydberg, pulse.detuning, field.Uniform
    )

    expected = PiecewiseLinear(
        times=[Decimal("0"), Decimal("1")],
        values=[Decimal("0.25"), Decimal("0.75")],
    )

    assert visitor.visit(wf1) == expected

    wf2 = piecewise_linear([1, 2, 3], [0, 1, 0, 1])[0.5:4.5]

    expected = PiecewiseLinear(
        [Decimal("0.0"), Decimal("0.5"), Decimal("2.5"), Decimal("4")],
        [Decimal("0.5"), Decimal("1.0"), Decimal("0.0"), Decimal("0.5")],
    )

    assert visitor.visit(wf2) == expected

    wf3 = waveform.Linear(0, 1, 2)[0.5:0.5]

    expected = PiecewiseLinear(
        [Decimal("0.0"), Decimal("0.0")], [Decimal("0.0"), Decimal("0.0")]
    )

    assert visitor.visit(wf3) == expected

    wf4 = piecewise_linear([1, 2, 3], [0, 1, 0, 1])[1.0:4.5]

    expected = PiecewiseLinear(
        [Decimal("0.0"), Decimal("2.0"), Decimal("3.5")],
        [Decimal("1.0"), Decimal("0.0"), Decimal("0.5")],
    )

    assert visitor.visit(wf4) == expected

    wf5 = piecewise_linear([1, 2, 3], [0, 1, 0, 1])[:3.0]

    expected = PiecewiseLinear(
        [Decimal("0.0"), Decimal("1.0"), Decimal("3.0")],
        [Decimal("0.0"), Decimal("1.0"), Decimal("0.0")],
    )
    assert visitor.visit(wf5) == expected

    wf5 = piecewise_linear([1, 2, 3], [0, 1, 0, 1])[0.5:3.0]

    expected = PiecewiseLinear(
        [Decimal("0.0"), Decimal("0.5"), Decimal("2.5")],
        [Decimal("0.5"), Decimal("1.0"), Decimal("0.0")],
    )
    assert visitor.visit(wf5) == expected


def test_waveform_slice_pwc():
    visitor = GeneratePiecewiseConstantChannel(
        sequence.rydberg, pulse.detuning, field.Uniform
    )

    wf1 = waveform.Constant(1, 2)[0.5:1.5]

    expected = PiecewiseConstant(
        times=[Decimal("0"), Decimal("1")],
        values=[Decimal("1"), Decimal("1")],
    )

    assert visitor.visit(wf1) == expected

    wf2 = piecewise_constant([1, 2, 3], [1, 2, 3])[0.5:4.5]

    expected = PiecewiseConstant(
        [Decimal("0.0"), Decimal("0.5"), Decimal("2.5"), Decimal("4")],
        [Decimal("1"), Decimal("2"), Decimal("3"), Decimal("3")],
    )

    assert visitor.visit(wf2) == expected

    wf3 = waveform.Constant(1, 2)[0.5:0.5]

    expected = PiecewiseConstant(
        [Decimal("0.0"), Decimal("0.0")], [Decimal("0"), Decimal("0")]
    )

    assert visitor.visit(wf3) == expected

    wf4 = piecewise_constant([1, 2, 3], [1, 2, 3])[1.0:4.5]

    expected = PiecewiseConstant(
        [Decimal("0.0"), Decimal("2.0"), Decimal("3.5")],
        [Decimal("2"), Decimal("3"), Decimal("3")],
    )

    assert visitor.visit(wf4) == expected

    wf5 = piecewise_constant([1, 2, 3], [1, 2, 3])[:3.0]

    expected = PiecewiseConstant(
        [Decimal("0.0"), Decimal("1.0"), Decimal("3.0")],
        [Decimal("1"), Decimal("2"), Decimal("2")],
    )

    assert visitor.visit(wf5) == expected

    wf5 = piecewise_constant([1, 2, 3], [1, 2, 3])[0.5:3.0]

    expected = PiecewiseConstant(
        [Decimal("0.0"), Decimal("0.5"), Decimal("2.5")],
        [Decimal("1"), Decimal("2"), Decimal("2")],
    )

    assert visitor.visit(wf5) == expected


def test_waveform_negative_pwl():
    wf = -waveform.Linear(0, 1, 2)

    visitor = GeneratePiecewiseLinearChannel(
        sequence.rydberg, pulse.detuning, field.Uniform
    )

    expected = PiecewiseLinear(
        times=[Decimal("0"), Decimal("2")],
        values=[Decimal("0"), Decimal("-1")],
    )

    assert visitor.visit(wf) == expected


def test_waveform_negative_pwc():
    wf = -piecewise_constant([1, 2, 3], [1, 2, 3])

    visitor = GeneratePiecewiseConstantChannel(
        sequence.rydberg, pulse.detuning, field.Uniform
    )

    expected = PiecewiseConstant(
        times=[Decimal("0"), Decimal("1"), Decimal("3"), Decimal("6")],
        values=[Decimal("-1"), Decimal("-2"), Decimal("-3"), Decimal("-3")],
    )

    assert visitor.visit(wf) == expected


def test_waveform_scale_pwl():
    wf = waveform.Linear(0, 1, 2) * 2

    visitor = GeneratePiecewiseLinearChannel(
        sequence.rydberg, pulse.detuning, field.Uniform
    )

    expected = PiecewiseLinear(
        times=[Decimal("0"), Decimal("2")],
        values=[Decimal("0"), Decimal("2")],
    )

    assert visitor.visit(wf) == expected


def test_waveform_scale_pwc():
    wf = piecewise_constant([1, 2, 3], [1, 2, 3]) * 2

    visitor = GeneratePiecewiseConstantChannel(
        sequence.rydberg, pulse.detuning, field.Uniform
    )

    expected = PiecewiseConstant(
        times=[Decimal("0"), Decimal("1"), Decimal("3"), Decimal("6")],
        values=[Decimal("2"), Decimal("4"), Decimal("6"), Decimal("6")],
    )

    assert visitor.visit(wf) == expected


def test_field_pwl():
    wf = piecewise_linear([1, 2, 3], [0, 1, 0, 1])
    f = field.Field({field.Uniform: wf})

    visitor = GeneratePiecewiseLinearChannel(
        sequence.rydberg, pulse.detuning, field.Uniform
    )

    expected = PiecewiseLinear(
        times=[Decimal("0"), Decimal("1"), Decimal("3"), Decimal("6")],
        values=[Decimal("0"), Decimal("1"), Decimal("0"), Decimal("1")],
    )

    assert visitor.visit(f) == expected


def test_field_pwc():
    wf = piecewise_constant([1, 2, 3], [1, 2, 3])
    f = field.Field({field.Uniform: wf})

    visitor = GeneratePiecewiseConstantChannel(
        sequence.rydberg, pulse.detuning, field.Uniform
    )

    expected = PiecewiseConstant(
        times=[Decimal("0"), Decimal("1"), Decimal("3"), Decimal("6")],
        values=[Decimal("1"), Decimal("2"), Decimal("3"), Decimal("3")],
    )

    assert visitor.visit(f) == expected


def test_pulse_leaf_pwl():
    wf = piecewise_linear([1, 2, 3], [0, 1, 0, 1])
    f = field.Field({field.Uniform: wf})
    p = pulse.Pulse({pulse.detuning: f})

    visitor = GeneratePiecewiseLinearChannel(
        sequence.rydberg, pulse.detuning, field.Uniform
    )

    expected = PiecewiseLinear(
        times=[Decimal("0"), Decimal("1"), Decimal("3"), Decimal("6")],
        values=[Decimal("0"), Decimal("1"), Decimal("0"), Decimal("1")],
    )

    assert visitor.visit(p) == expected


def test_pulse_leaf_pwc():
    wf = piecewise_constant([1, 2, 3], [1, 2, 3])
    f = field.Field({field.Uniform: wf})
    p = pulse.Pulse({pulse.detuning: f})

    visitor = GeneratePiecewiseConstantChannel(
        sequence.rydberg, pulse.detuning, field.Uniform
    )

    expected = PiecewiseConstant(
        times=[Decimal("0"), Decimal("1"), Decimal("3"), Decimal("6")],
        values=[Decimal("1"), Decimal("2"), Decimal("3"), Decimal("3")],
    )

    assert visitor.visit(p) == expected


def test_pulse_named_pwl():
    wf = piecewise_linear([1, 2, 3], [0, 1, 1, 0])
    f = field.Field({field.Uniform: wf})
    p = pulse.NamedPulse("test", pulse.Pulse({pulse.detuning: f}))

    visitor = GeneratePiecewiseLinearChannel(
        sequence.rydberg, pulse.detuning, field.Uniform
    )

    expected = PiecewiseLinear(
        times=[Decimal("0"), Decimal("1"), Decimal("3"), Decimal("6")],
        values=[Decimal("0"), Decimal("1"), Decimal("1"), Decimal("0")],
    )

    assert visitor.visit(p) == expected


def test_pulse_named_pwc():
    wf = piecewise_constant([1, 2, 3], [1, 2, 3])
    f = field.Field({field.Uniform: wf})
    p = pulse.NamedPulse("test", pulse.Pulse({pulse.detuning: f}))

    visitor = GeneratePiecewiseConstantChannel(
        sequence.rydberg, pulse.detuning, field.Uniform
    )

    expected = PiecewiseConstant(
        times=[Decimal("0"), Decimal("1"), Decimal("3"), Decimal("6")],
        values=[Decimal("1"), Decimal("2"), Decimal("3"), Decimal("3")],
    )

    assert visitor.visit(p) == expected


def test_pulse_slice_pwl():
    wf = piecewise_linear([1, 2, 3], [0, 1, 0, 1])
    f = field.Field({field.Uniform: wf})
    p = pulse.Pulse({pulse.detuning: f})[1.0:4.5]

    visitor = GeneratePiecewiseLinearChannel(
        sequence.rydberg, pulse.detuning, field.Uniform
    )

    expected = PiecewiseLinear(
        [Decimal("0.0"), Decimal("2.0"), Decimal("3.5")],
        [Decimal("1.0"), Decimal("0.0"), Decimal("0.5")],
    )

    assert visitor.visit(p) == expected


def test_pulse_slice_pwc():
    wf = piecewise_constant([1, 2, 3], [1, 2, 3])
    f = field.Field({field.Uniform: wf})
    p = pulse.Pulse({pulse.detuning: f})[1.0:4.5]

    visitor = GeneratePiecewiseConstantChannel(
        sequence.rydberg, pulse.detuning, field.Uniform
    )

    expected = PiecewiseConstant(
        [Decimal("0.0"), Decimal("2.0"), Decimal("3.5")],
        [Decimal("2"), Decimal("3"), Decimal("3")],
    )

    assert visitor.visit(p) == expected


def test_pulse_append_pwl():
    wf = piecewise_linear([1, 2, 3], [0, 1, 1, 0])
    f = field.Field({field.Uniform: wf})
    p = pulse.Pulse({pulse.detuning: f})
    p = p.append(p)

    visitor = GeneratePiecewiseLinearChannel(
        sequence.rydberg, pulse.detuning, field.Uniform
    )

    expected = PiecewiseLinear(
        [
            Decimal("0.0"),
            Decimal("1.0"),
            Decimal("3.0"),
            Decimal("6.0"),
            Decimal("7.0"),
            Decimal("9.0"),
            Decimal("12.0"),
        ],
        [
            Decimal("0.0"),
            Decimal("1.0"),
            Decimal("1.0"),
            Decimal("0.0"),
            Decimal("1.0"),
            Decimal("1.0"),
            Decimal("0.0"),
        ],
    )

    assert visitor.visit(p) == expected


def test_pulse_append_pwc():
    wf = piecewise_constant([1, 2, 3], [1, 2, 3])
    f = field.Field({field.Uniform: wf})
    p = pulse.Pulse({pulse.detuning: f})
    p = p.append(p)

    visitor = GeneratePiecewiseConstantChannel(
        sequence.rydberg, pulse.detuning, field.Uniform
    )

    expected = PiecewiseConstant(
        [
            Decimal("0.0"),
            Decimal("1.0"),
            Decimal("3.0"),
            Decimal("6.0"),
            Decimal("7.0"),
            Decimal("9.0"),
            Decimal("12.0"),
        ],
        [
            Decimal("1"),
            Decimal("2"),
            Decimal("3"),
            Decimal("1"),
            Decimal("2"),
            Decimal("3"),
            Decimal("3"),
        ],
    )

    assert visitor.visit(p) == expected


def test_sequence_leaf_pwl():
    wf = piecewise_linear([1, 2, 3], [0, 1, 0, 1])
    f = field.Field({field.Uniform: wf})
    p = pulse.Pulse({pulse.detuning: f})
    s = sequence.Sequence({sequence.rydberg: p})

    visitor = GeneratePiecewiseLinearChannel(
        sequence.rydberg, pulse.detuning, field.Uniform
    )

    expected = PiecewiseLinear(
        times=[Decimal("0"), Decimal("1"), Decimal("3"), Decimal("6")],
        values=[Decimal("0"), Decimal("1"), Decimal("0"), Decimal("1")],
    )

    assert visitor.visit(s) == expected


def test_sequence_leaf_pwc():
    wf = piecewise_constant([1, 2, 3], [1, 2, 3])
    f = field.Field({field.Uniform: wf})
    p = pulse.Pulse({pulse.detuning: f})
    s = sequence.Sequence({sequence.rydberg: p})

    visitor = GeneratePiecewiseConstantChannel(
        sequence.rydberg, pulse.detuning, field.Uniform
    )

    expected = PiecewiseConstant(
        times=[Decimal("0"), Decimal("1"), Decimal("3"), Decimal("6")],
        values=[Decimal("1"), Decimal("2"), Decimal("3"), Decimal("3")],
    )

    assert visitor.visit(s) == expected


def test_sequence_named_pwl():
    wf = piecewise_linear([1, 2, 3], [0, 1, 1, 0])
    f = field.Field({field.Uniform: wf})
    p = pulse.Pulse({pulse.detuning: f})
    s = sequence.NamedSequence("test", sequence.Sequence({sequence.rydberg: p}))

    visitor = GeneratePiecewiseLinearChannel(
        sequence.rydberg, pulse.detuning, field.Uniform
    )

    expected = PiecewiseLinear(
        times=[Decimal("0"), Decimal("1"), Decimal("3"), Decimal("6")],
        values=[Decimal("0"), Decimal("1"), Decimal("1"), Decimal("0")],
    )

    assert visitor.visit(s) == expected


def test_sequence_named_pwc():
    wf = piecewise_constant([1, 2, 3], [1, 2, 3])
    f = field.Field({field.Uniform: wf})
    p = pulse.Pulse({pulse.detuning: f})
    s = sequence.NamedSequence("test", sequence.Sequence({sequence.rydberg: p}))

    visitor = GeneratePiecewiseConstantChannel(
        sequence.rydberg, pulse.detuning, field.Uniform
    )

    expected = PiecewiseConstant(
        times=[Decimal("0"), Decimal("1"), Decimal("3"), Decimal("6")],
        values=[Decimal("1"), Decimal("2"), Decimal("3"), Decimal("3")],
    )

    assert visitor.visit(s) == expected


def test_sequence_slice_pwl():
    wf = piecewise_linear([1, 2, 3], [0, 1, 0, 1])
    f = field.Field({field.Uniform: wf})
    p = pulse.Pulse({pulse.detuning: f})
    s = sequence.Sequence({sequence.rydberg: p})[1.0:4.5]

    visitor = GeneratePiecewiseLinearChannel(
        sequence.rydberg, pulse.detuning, field.Uniform
    )

    expected = PiecewiseLinear(
        [Decimal("0.0"), Decimal("2.0"), Decimal("3.5")],
        [Decimal("1.0"), Decimal("0.0"), Decimal("0.5")],
    )

    assert visitor.visit(s) == expected


def test_sequence_slice_pwc():
    wf = piecewise_constant([1, 2, 3], [1, 2, 3])
    f = field.Field({field.Uniform: wf})
    p = pulse.Pulse({pulse.detuning: f})
    s = sequence.Sequence({sequence.rydberg: p})[1.0:4.5]

    visitor = GeneratePiecewiseConstantChannel(
        sequence.rydberg, pulse.detuning, field.Uniform
    )

    expected = PiecewiseConstant(
        [Decimal("0.0"), Decimal("2.0"), Decimal("3.5")],
        [Decimal("2"), Decimal("3"), Decimal("3")],
    )

    assert visitor.visit(s) == expected


def test_sequence_append_pwl():
    wf = piecewise_linear([1, 2, 3], [0, 1, 1, 0])
    f = field.Field({field.Uniform: wf})
    p = pulse.Pulse({pulse.detuning: f})
    s = sequence.Sequence({sequence.rydberg: p})
    s = s.append(s)

    visitor = GeneratePiecewiseLinearChannel(
        sequence.rydberg, pulse.detuning, field.Uniform
    )

    expected = PiecewiseLinear(
        [
            Decimal("0.0"),
            Decimal("1.0"),
            Decimal("3.0"),
            Decimal("6.0"),
            Decimal("7.0"),
            Decimal("9.0"),
            Decimal("12.0"),
        ],
        [
            Decimal("0.0"),
            Decimal("1.0"),
            Decimal("1.0"),
            Decimal("0.0"),
            Decimal("1.0"),
            Decimal("1.0"),
            Decimal("0.0"),
        ],
    )

    assert visitor.visit(s) == expected


def test_sequence_append_pwc():
    wf = piecewise_constant([1, 2, 3], [1, 2, 3])
    f = field.Field({field.Uniform: wf})
    p = pulse.Pulse({pulse.detuning: f})
    s = sequence.Sequence({sequence.rydberg: p})
    s = s.append(s)

    visitor = GeneratePiecewiseConstantChannel(
        sequence.rydberg, pulse.detuning, field.Uniform
    )

    expected = PiecewiseConstant(
        [
            Decimal("0.0"),
            Decimal("1.0"),
            Decimal("3.0"),
            Decimal("6.0"),
            Decimal("7.0"),
            Decimal("9.0"),
            Decimal("12.0"),
        ],
        [
            Decimal("1"),
            Decimal("2"),
            Decimal("3"),
            Decimal("1"),
            Decimal("2"),
            Decimal("3"),
            Decimal("3"),
        ],
    )

    assert visitor.visit(s) == expected


def test_analog_circuit_pwl():
    wf = piecewise_linear([1, 2, 3], [0, 1, 0, 1])
    f = field.Field({field.Uniform: wf})
    p = pulse.Pulse({pulse.detuning: f})
    s = sequence.Sequence({sequence.rydberg: p})
    c = analog_circuit.AnalogCircuit(start.add_position((0, 0)), s)

    visitor = GeneratePiecewiseLinearChannel(
        sequence.rydberg, pulse.detuning, field.Uniform
    )

    expected = PiecewiseLinear(
        times=[Decimal("0"), Decimal("1"), Decimal("3"), Decimal("6")],
        values=[Decimal("0"), Decimal("1"), Decimal("0"), Decimal("1")],
    )

    assert visitor.visit(c) == expected


def test_analog_circuit_pwc():
    wf = piecewise_constant([1, 2, 3], [1, 2, 3])
    f = field.Field({field.Uniform: wf})
    p = pulse.Pulse({pulse.detuning: f})
    s = sequence.Sequence({sequence.rydberg: p})
    c = analog_circuit.AnalogCircuit(start.add_position((0, 0)), s)

    visitor = GeneratePiecewiseConstantChannel(
        sequence.rydberg, pulse.detuning, field.Uniform
    )

    expected = PiecewiseConstant(
        times=[Decimal("0"), Decimal("1"), Decimal("3"), Decimal("6")],
        values=[Decimal("1"), Decimal("2"), Decimal("3"), Decimal("3")],
    )

    assert visitor.visit(c) == expected


def test_lattice_site_coefficients_codegen():
    wf = piecewise_linear([1, 2, 3], [0, 1, 0, 1])
    
    mask = [Decimal("0"), Decimal("1"), Decimal("0")]
    f = field.Field({field.AssignedRunTimeVector("mask", mask): wf})
    p = pulse.Pulse({pulse.detuning: f})
    s = sequence.Sequence({sequence.rydberg: p})
    c = analog_circuit.AnalogCircuit(start.add_position([(0, 0),(1,1), (2, 2)]), s)
    
    
