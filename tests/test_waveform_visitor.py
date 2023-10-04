# from bloqade import start
from bloqade.ir import rabi
from bloqade.ir import cast
from bloqade.ir import Interpolation
from bloqade.ir import Interval
from bloqade.ir.visitor.waveform import WaveformVisitor
from bloqade.ir.control.waveform import (
    GaussianKernel,
    Alignment,
    Linear,
    Constant,
    Append,
    Slice,
    Negative,
    Scale,
    Add,
    Record,
    PythonFn,
    Sample,
    Poly,
    Smooth,
    AlignedWaveform,
)
import pytest


wv_linear = Linear(start=0, stop=4, duration=0.1)
wv_constant = Constant(value=0, duration=0.1)
wv_append = Append([wv_linear, wv_constant])
wv_slice = Slice(waveform=wv_linear, interval=Interval(cast(0.1), cast(0.2)))
wv_negative = Negative(wv_linear)
wv_scale = Scale(cast(4), wv_linear)
wv_add = Add(wv_linear, wv_constant)
wv_record = Record(wv_linear, cast("tst"))
wv_python = PythonFn.create(lambda x: x**2, duration=0.5)
wv_sample = Sample(wv_linear, Interpolation("linear"), dt=cast(0.5))
wv_poly = Poly(coeffs=[0.1, 0.2], duration=0.5)
wv_smooth = Smooth(radius=cast(0.5), kernel=GaussianKernel, waveform=wv_linear)
wv_align = AlignedWaveform(wv_linear, Alignment("left_aligned"), cast(0.5))


def test_base_wvfm_visitor():
    wvis = WaveformVisitor()

    with pytest.raises(NotImplementedError):
        wvis.visit(wv_align)

    with pytest.raises(NotImplementedError):
        wvis.visit(wv_linear)

    with pytest.raises(NotImplementedError):
        wvis.visit(wv_constant)

    with pytest.raises(NotImplementedError):
        wvis.visit(wv_append)

    with pytest.raises(NotImplementedError):
        wvis.visit(wv_slice)

    with pytest.raises(NotImplementedError):
        wvis.visit(wv_negative)

    with pytest.raises(NotImplementedError):
        wvis.visit(wv_scale)

    with pytest.raises(NotImplementedError):
        wvis.visit(wv_add)

    with pytest.raises(NotImplementedError):
        wvis.visit(wv_record)

    with pytest.raises(NotImplementedError):
        wvis.visit(wv_python)

    with pytest.raises(NotImplementedError):
        wvis.visit(wv_sample)

    with pytest.raises(NotImplementedError):
        wvis.visit(wv_poly)

    with pytest.raises(NotImplementedError):
        wvis.visit(wv_smooth)

    ## not waveform ast
    with pytest.raises(ValueError):
        wvis.visit(rabi)
