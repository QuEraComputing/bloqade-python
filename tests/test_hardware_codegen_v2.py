import pytest
from bloqade.ir.control import waveform, field, pulse, sequence
from bloqade.ir import analog_circuit
from bloqade.codegen.hardware_v2.piecewise_linear import (
    PiecewiseLinear,
    GeneratePiecewiseLinearChannel,
)
from bloqade import piecewise_linear, start
import numpy as np
from decimal import Decimal


@waveform.to_waveform(4.0)
def wf(t):
    return np.sin(t)


def test_error():
    with pytest.raises(TypeError):
        GeneratePiecewiseLinearChannel(
            sequence.rydberg, pulse.detuning, field.Uniform
        ).visit(wf)


def test_waveform_append():
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


def test_waveform_sample():
    visitor = GeneratePiecewiseLinearChannel(
        sequence.rydberg, pulse.detuning, field.Uniform
    )

    pwl_wf = wf.sample(0.1, waveform.Interpolation.Linear)

    times, values = pwl_wf.samples()

    expected = PiecewiseLinear(times=times, values=values)

    assert visitor.visit(pwl_wf) == expected


def test_waveform_add():
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


def test_waveform_slice():
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

    # assert False


def test_waveform_negative():
    wf = -waveform.Linear(0, 1, 2)

    visitor = GeneratePiecewiseLinearChannel(
        sequence.rydberg, pulse.detuning, field.Uniform
    )

    expected = PiecewiseLinear(
        times=[Decimal("0"), Decimal("2")],
        values=[Decimal("0"), Decimal("-1")],
    )

    assert visitor.visit(wf) == expected


def test_waveform_scale():
    wf = waveform.Linear(0, 1, 2) * 2

    visitor = GeneratePiecewiseLinearChannel(
        sequence.rydberg, pulse.detuning, field.Uniform
    )

    expected = PiecewiseLinear(
        times=[Decimal("0"), Decimal("2")],
        values=[Decimal("0"), Decimal("2")],
    )

    assert visitor.visit(wf) == expected


def test_field():
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


def test_pulse_leaf():
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


def test_pulse_named():
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


def test_pulse_slice():
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


def test_pulse_append():
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


def test_sequence_leaf():
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


def test_sequence_named():
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


def test_sequence_slice():
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


def test_sequence_append():
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


def test_analog_circuit():
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
