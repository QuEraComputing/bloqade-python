from bloqade.ir import (
    Linear,
    Constant,
    Poly,
    Record,
    # AlignedWaveform,
    # Alignment,
    # AlignedValue,
    instruction,
    GaussianKernel,
    LogisticKernel,
    SigmoidKernel,
    TriangleKernel,
    UniformKernel,
    ParabolicKernel,
    BiweightKernel,
    TriweightKernel,
    TricubeKernel,
    CosineKernel,
)
from bloqade import cast
from bloqade.ir.control.waveform import PythonFn, Append
from bloqade.ir.control.waveform import SmoothingKernel
from decimal import Decimal
import pytest
import numpy as np


def test_wvfm_linear():
    wf = Linear(start=1.0, stop=2.0, duration=3.0)

    assert wf.print_node() == "Linear"
    assert wf.eval_decimal(clock_s=Decimal("6.0")) == 0

    assert wf.children() == {
        "start": cast(1.0),
        "stop": cast(2.0),
        "duration": cast(3.0),
    }


def test_wvfm_constant():
    wf = Constant(value=1.0, duration=3.0)

    assert wf.print_node() == "Constant"
    assert wf.eval_decimal(clock_s=Decimal("6.0")) == 0
    assert wf.children() == {"value": cast(1.0), "duration": cast(3.0)}


def test_wvfm_pyfn():
    def my_func(time, *, omega, phi=0, amplitude):
        import numpy as np

        return amplitude * np.cos(omega * time + phi)

    @instruction(duration=1.0)
    def annot_my_func(time, *, omega, phi=0, amplitude):
        import numpy as np

        return amplitude * np.cos(omega * time + phi)

    ## have varargs:
    def my_func2(time, *omega):
        return time

    ## have varkw:
    def my_func3(time, omega, **phi):
        return time

    with pytest.raises(ValueError):
        PythonFn(my_func2, duration=1.0)

    with pytest.raises(ValueError):
        PythonFn(my_func3, duration=1.0)

    wf = PythonFn(my_func, duration=1.0)
    awf = annot_my_func

    assert wf.eval_decimal(Decimal("0.56"), omega=1, amplitude=4) == awf.eval_decimal(
        Decimal("0.56"), omega=1, amplitude=4
    )

    assert wf.eval_decimal(Decimal("3"), omega=1, amplitude=4) == Decimal(0)

    assert wf.print_node() == "PythonFn: my_func"
    assert wf.children() == {"duration": cast(1.0)}


def test_wvfm_app():
    wf = Linear(start=1.0, stop=2.0, duration=3.0)
    wf2 = Constant(value=1.0, duration=3.0)

    wf3 = Append([wf, wf2])

    assert wf3.print_node() == "Append"
    assert wf3.children() == [wf, wf2]


def test_wvfm_neg():
    wf = Constant(value=1.0, duration=3.0)
    wf2 = -wf

    assert wf2.print_node() == "-"
    assert wf2.children() == [wf]
    assert wf2.__repr__() == "-(" + wf2.children()[0].__repr__() + ")"

    assert wf2.eval_decimal(Decimal("0.5")) == Decimal("-1.0")


def test_wvfm_scale():
    wf = Constant(value=1.0, duration=3.0)
    wf2 = 2.0 * wf

    assert wf2.print_node() == "Scale"
    assert wf2.children() == [cast(2.0), wf]
    assert wf2.__repr__() == "(2.0 * %s)" % (wf.__repr__())

    assert wf2.eval_decimal(Decimal("0.5")) == Decimal("2.0")

    wf3 = wf * 2.0
    assert wf3.print_node() == "Scale"
    assert wf3.children() == [cast(2.0), wf]
    assert wf3.__repr__() == "(2.0 * %s)" % (wf.__repr__())

    assert wf3.eval_decimal(Decimal("0.5")) == Decimal("2.0")


def test_wvfn_add():
    wf = Constant(value=1.0, duration=3.0)
    wf2 = Linear(start=1.0, stop=2.0, duration=2.0)

    wf3 = wf + wf2

    assert wf3.print_node() == "+"
    assert wf3.children() == [wf, wf2]
    assert wf3.__repr__() == "(%s + %s)" % (wf.__repr__(), wf2.__repr__())

    assert wf3.eval_decimal(Decimal("0")) == Decimal("2.0")
    assert wf3.eval_decimal(Decimal("2.5")) == Decimal("1.0")


def test_wvfn_rec():
    wf = Linear(start=1.0, stop=2.0, duration=3.0)

    re = Record(wf, cast("tst"))

    assert re.print_node() == "Record"
    assert re.children() == {"Waveform": wf, "Variable": cast("tst")}
    assert re.__repr__() == "Record(%s, %s)" % (wf.__repr__(), cast("tst").__repr__())

    assert re.eval_decimal(Decimal("0")) == Decimal("1.0")


def test_wvfn_poly():
    wf = Poly(checkpoints=[cast(1), cast(2), cast(3)], duration=10)

    assert wf.print_node() == "Poly"
    assert wf.children() == {
        "b": wf.checkpoints[0],
        "t": wf.checkpoints[1],
        "t^2": wf.checkpoints[2],
        "duration": cast(10),
    }
    assert wf.eval_decimal(Decimal("0.5")) == (1) + (2) * 0.5 + (3) * 0.5**2


##-----------------------------


def test_smkern_base():
    ker = SmoothingKernel()

    with pytest.raises(NotImplementedError):
        ker(0.5)


def test_smkern_gauss():
    ker = GaussianKernel
    assert ker(0.5) == np.exp(-(0.5**2) / 2) / np.sqrt(2 * np.pi)


def test_smkern_logist():
    ker = LogisticKernel
    assert ker(0.5) == np.exp(-(np.logaddexp(0, 0.5) + np.logaddexp(0, -0.5)))


def test_smkern_sigmoid():
    ker = SigmoidKernel
    assert ker(0.5) == (2 / np.pi) * np.exp(-np.logaddexp(-0.5, 0.5))


def test_smkern_triangle():
    ker = TriangleKernel
    assert ker(0.5) == np.maximum(0, 1 - np.abs(0.5))


def test_smkern_uniform():
    ker = UniformKernel
    assert ker(0.5) == 1.0


def test_smkern_parab():
    ker = ParabolicKernel
    assert ker(0.5) == (3 / 4) * np.maximum(0, 1 - 0.5**2)


def test_smkern_biweight():
    ker = BiweightKernel
    assert ker(0.5) == (15 / 16) * np.maximum(0, 1 - 0.5**2) ** 2


def test_smkern_triweight():
    ker = TriweightKernel
    assert ker(0.5) == (35 / 32) * np.maximum(0, 1 - 0.5**2) ** 3


def test_smkern_tricube():
    ker = TricubeKernel
    assert ker(0.5) == (70 / 81) * np.maximum(0, 1 - np.abs(0.5) ** 3) ** 3


def test_smkern_cosine():
    ker = CosineKernel
    assert ker(0.5) == (np.pi / 4) * np.cos(np.pi * 0.5 / 2)


def test_wvfn_smooth():
    wv = Linear(start=1.0, stop=2.0, duration=3.0)
    wf = wv.smooth(radius=0.5, kernel=GaussianKernel)

    assert wf.duration == cast(3.0)
    assert wf.__repr__() == "Smooth(kernel=%s, waveform=%s)" % (
        GaussianKernel.__repr__(),
        wv.__repr__(),
    )

    assert wf.eval_decimal(Decimal("0.1")) == 1.0844831620655968


"""
print(wf[:0.5].duration)
print(wf[1.0:].duration)
print(wf[0.2:0.8].duration)

print(-wf)
print(wf.scale(1.0))

eval(repr(-wf))
eval(repr(wf.scale(1.0)))

# canonicalize append
wf = (
    Linear(0.0, "rabi_amplitude_max", "up_time")
    .append(Constant("rabi_amplitude_max", "anneal_time"))
    .append(Linear("rabi_amplitude_max", 0.0, "up_time"))
)
print(wf)

smooth_wf = wf.smooth(0.1, GaussianKernel)
print(smooth_wf(1.0, rabi_amplitude_max=1.0, up_time=1.0, anneal_time=1.0))
smooth_wf = wf.smooth(0.1, BiweightKernel)
print(smooth_wf(1.0, rabi_amplitude_max=1.0, up_time=1.0, anneal_time=1.0))

# try scaling
wf * scalar.Literal(5.0)

# try addition
wf + wf

# polynomial
Poly(
    [scalar.Literal(10) + scalar.Variable("l"), scalar.Literal(5), scalar.Literal(-2)],
    scalar.Variable("g"),
)

# Record
Record(wf, scalar.Variable("n"))

AlignedWaveform(wf, Alignment.Left, AlignedValue.Right)
"""
# eval(repr(wf))

# print(wf)

# wf = wf.append(wf)
# eval(repr(wf))
# print(wf)

# wf = Linear(0.0, "rabi_amplitude_max", "up_time").append(wf)
# eval(repr(wf))
# print(wf)
