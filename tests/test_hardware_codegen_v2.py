import pytest
from bloqade.ir.control import waveform, field, pulse, sequence
from bloqade.codegen.hardware_v2.piecewise_linear import (
    PiecewiseLinear,
    GeneratePiecewiseLinearChannel,
)
from bloqade import piecewise_linear
import numpy as np
from decimal import Decimal


def convert_to_decimal(value):
    return Decimal(str(value))


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
    @waveform.to_waveform(4.0)
    def wf(t):
        return np.sin(t)

    with pytest.raises(TypeError):
        GeneratePiecewiseLinearChannel(
            sequence.rydberg, pulse.detuning, field.Uniform
        ).visit(wf)

    visitor = GeneratePiecewiseLinearChannel(
        sequence.rydberg, pulse.detuning, field.Uniform
    )

    pwl_wf = wf.sample(0.1, waveform.Interpolation.Linear)

    times, values = pwl_wf.samples()

    expected = PiecewiseLinear(times=times, values=values)

    assert visitor.visit(pwl_wf) == expected


def test_waveform_lowering_add():
    left = waveform.Linear(0, 1, 2)
    right = piecewise_linear(
        [1, 1],
        [0, 1, 0],
    )
    wf = left + right

    visitor = GeneratePiecewiseLinearChannel(
        sequence.rydberg, pulse.detuning, field.Uniform
    )

    expected = PiecewiseLinear(
        times=[Decimal("0"), Decimal("1"), Decimal("2")],
        values=[Decimal("0"), Decimal("1.5"), Decimal("1.0")],
    )

    assert visitor.visit(wf) == expected
