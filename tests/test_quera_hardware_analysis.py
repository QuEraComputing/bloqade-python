import pytest
from bloqade.analysis.hardware.quera import (
    ValidatePiecewiseLinearChannel,
    ValidatePiecewiseConstantChannel,
)
from bloqade.transform.common.flatten_sequence import FillMissingWaveforms

import bloqade.ir.control.sequence as sequence
import bloqade.ir.control.pulse as pulse
import bloqade.ir.control.field as field
import bloqade.ir.control.waveform as waveform

from bloqade import piecewise_constant, piecewise_linear


@waveform.to_waveform(1)
def py_func(x):
    return x


def test_piecewise_constant_happy_path():
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


def test_piecewise_constant_sad_path():
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


def test_piecewise_linear_happy_path():
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


def test_piecewise_linear_sad_path():
    validator = ValidatePiecewiseLinearChannel(
        level_coupling=sequence.rydberg,
        field_name=pulse.rabi.amplitude,
        spatial_modulations=field.Uniform,
    )

    wf1 = py_func
    wf2 = py_func.sample(0.1, "constant")
    wf3 = waveform.Poly([1, 2, 3], 1)
    wf4 = py_func.smooth(1, "Gaussian")
    wf5 = FillMissingWaveforms().visit(
        waveform.Linear(1, 2, 0.5) + waveform.Linear(2, 3, 1)
    )
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
