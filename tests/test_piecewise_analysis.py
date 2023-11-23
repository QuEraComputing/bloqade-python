from decimal import Decimal
import pytest
from bloqade.analysis.hardware.piecewise_constant import PiecewiseConstantValidator
from bloqade.analysis.hardware.piecewise_linear import PiecewiseLinearValidator
import bloqade.ir.control.waveform as waveform
from bloqade import piecewise_constant, piecewise_linear, cast


@waveform.to_waveform(1)
def py_func(x):
    return x


def test_piecewise_constant_happy_path():
    validator = PiecewiseConstantValidator()

    wf1 = waveform.Constant(1, 1)
    wf2 = waveform.Linear(1, 1, 1)
    wf3 = waveform.Poly([], 1)
    wf4 = waveform.Poly([1], 1)
    wf5 = py_func.sample(0.1, "constant")
    wf6 = waveform.Constant(1, 1).smooth(1, "Gaussian")

    assert validator.scan(wf1) is None
    assert validator.scan(wf2) is None
    assert validator.scan(wf3) is None
    assert validator.scan(wf4) is None
    assert validator.scan(wf5) is None
    assert validator.scan(wf6) is None
    assert validator.scan(wf1.append(wf2).append(wf3)) is None


def test_piecewise_constant_sad_path():
    validator = PiecewiseConstantValidator()

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


def test_piecewise_linear_happy_path():
    validator = PiecewiseLinearValidator()

    wf1 = waveform.Constant(1, 1)
    wf2 = waveform.Linear(1, 2, 1)
    wf3 = waveform.Poly([], 1)
    wf4 = waveform.Poly([1], 1)
    wf5 = waveform.Poly([1, 2], 1)
    wf6 = py_func.sample(0.1, "linear")
    wf7 = piecewise_linear([0.1, 0.2, 0.3], [1, 2, 3, 4])
    wf8 = wf7[0.05:0.25]
    wf9 = wf1 + wf2

    res = validator.scan(wf1)

    assert res.duration_expr == cast(1)
    assert res.start_expr == cast(1)
    assert res.stop_expr == cast(1)

    res = validator.scan(wf2)

    assert res.duration_expr == cast(1)
    assert res.start_expr == cast(1)
    assert res.stop_expr == cast(2)

    res = validator.scan(wf3)

    assert res.duration_expr == cast(1)
    assert res.start_expr == cast(0)
    assert res.stop_expr == cast(0)

    res = validator.scan(wf4)

    assert res.duration_expr == cast(1)
    assert res.start_expr == cast(1)
    assert res.stop_expr == cast(1)

    res = validator.scan(wf5)

    assert res.duration_expr == cast(1)
    assert res.start_expr == cast(1)
    assert res.stop_expr == cast(3)

    res = validator.scan(wf6)

    assert res.duration_expr == cast(1)
    assert res.start_expr == wf6
    assert res.stop_expr == wf6

    res = validator.scan(wf7)

    assert res.duration_expr == cast(0.6)
    assert res.start_expr == cast(1)
    assert res.stop_expr == cast(4)

    res = validator.scan(wf8)

    assert res.duration_expr == cast(0.6)[0.05:0.25]
    assert res.start_expr == wf8
    assert res.stop_expr == wf8

    res = validator.scan(wf9)

    assert res.duration_expr == cast(1)
    assert res.start_expr == wf9
    assert res.stop_expr == wf9
    assert res.start == wf9.eval_decimal(Decimal("0"))
    assert res.stop == wf9.eval_decimal(Decimal("1"))


def test_piecewise_linear_sad_path():
    validator = PiecewiseLinearValidator()

    wf1 = py_func
    wf2 = py_func.sample(0.1, "constant")
    wf3 = waveform.Poly([1, 2, 3], 1)
    wf4 = py_func.smooth(1, "Gaussian")
    wf5 = waveform.Linear(1, 2, 0.5) + waveform.Linear(2, 3, 1)
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
