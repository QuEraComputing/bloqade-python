from bloqade.ir import (
    Linear,
    Constant,
    Poly,
    Record,
    AlignedWaveform,
    Alignment,
    Side,
    to_waveform,
    Interpolation,
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
from bloqade.ir.scalar import Interval
from bloqade.ir.control.waveform import PythonFn, Append, Slice, Sample
from bloqade.ir.control.waveform import SmoothingKernel, Waveform
from decimal import Decimal
import pytest
import numpy as np
from io import StringIO
from IPython.lib.pretty import PrettyPrinter as PP
import bloqade.ir.tree_print as trp

trp.color_enabled = False


def test_wvfm_base():
    wf = Waveform()
    with pytest.raises(NotImplementedError):
        wf.eval_decimal(Decimal("0.5"))


def test_wvfm_linear():
    wf = Linear(start=1.0, stop=2.0, duration=3.0)

    assert wf.print_node() == "Linear"
    assert wf.eval_decimal(clock_s=Decimal("6.0")) == 0
    assert isinstance(hash(wf), int)

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
    assert isinstance(hash(wf), int)

    mystdout = StringIO()
    p = PP(mystdout)

    wf._repr_pretty_(p, 0)

    assert (
        mystdout.getvalue()
        == "Constant\n"
        + "├─ value\n"
        + "│  ⇒ Literal: 1.0\n"
        + "⋮\n"
        + "└─ duration\n"
        + "   ⇒ Literal: 3.0⋮\n"
    )


def test_wvfm_pyfn():
    def my_func(time, *, omega, phi=0, amplitude):
        import numpy as np

        return amplitude * np.cos(omega * time + phi)

    @to_waveform(duration=1.0)
    def annot_my_func(time, *, omega, phi=0, amplitude):
        import numpy as np

        return amplitude * np.cos(omega * time + phi)

    ## have varargs:
    def my_func2(time, *omega):
        return time

    assert my_func2(3) == 3

    ## have varkw:
    def my_func3(time, omega, **phi):
        return time

    assert my_func3(3, 2) == 3

    with pytest.raises(ValueError):
        PythonFn.create(my_func2, duration=1.0)

    with pytest.raises(ValueError):
        PythonFn.create(my_func3, duration=1.0)

    wf = PythonFn.create(my_func, duration=1.0)
    awf = annot_my_func

    assert wf.eval_decimal(Decimal("0.56"), omega=1, amplitude=4) == awf.eval_decimal(
        Decimal("0.56"), omega=1, amplitude=4
    )

    assert wf.eval_decimal(Decimal("3"), omega=1, amplitude=4) == Decimal(0)

    assert wf.print_node() == "PythonFn: my_func"
    assert wf.children() == {
        "duration": cast(1.0),
        "omega": cast("omega"),
        "phi": cast("phi"),
        "amplitude": cast("amplitude"),
    }
    assert wf.duration == cast(1.0)
    assert isinstance(hash(wf), int)

    mystdout = StringIO()
    p = PP(mystdout)

    wf._repr_pretty_(p, 0)

    assert mystdout.getvalue() == (
        "PythonFn: my_func\n"
        + "├─ duration\n"
        + "│  ⇒ Literal: 1.0\n⋮\n"
        + "├─ phi\n"
        + "│  ⇒ Variable: phi\n⋮\n"
        + "├─ omega\n"
        + "│  ⇒ Variable: omega\n⋮\n"
        + "└─ amplitude\n"
        + "   ⇒ Variable: amplitude⋮\n"
    )


def test_wvfm_app():
    wf = Linear(start=1.0, stop=2.0, duration=3.0)
    wf2 = Constant(value=1.0, duration=3.0)

    wf3 = Append([wf, wf2])

    assert wf3.print_node() == "Append"
    assert wf3.children() == (wf, wf2)
    assert wf3.eval_decimal(Decimal(10)) == Decimal(0)
    assert isinstance(hash(wf), int)

    mystdout = StringIO()
    p = PP(mystdout)

    wf3._repr_pretty_(p, 0)

    assert (
        mystdout.getvalue()
        == "Append\n" + "├─ Linear\n" + "⋮\n" + "└─ Constant\n" + "⋮\n"
    )


def test_wvfm_neg():
    wf = Constant(value=1.0, duration=3.0)
    wf2 = -wf

    assert wf2.print_node() == "Negative"
    assert wf2.children() == [wf]
    assert isinstance(hash(wf), int)

    assert wf2.eval_decimal(Decimal("0.5")) == Decimal("-1.0")

    mystdout = StringIO()
    p = PP(mystdout)

    wf2._repr_pretty_(p, 2)

    assert (
        mystdout.getvalue()
        == "Negative\n"
        + "└─ Constant\n"
        + "   ├─ value\n"
        + "   │  ⇒ Literal: 1.0\n"
        + "   └─ duration\n"
        + "      ⇒ Literal: 3.0"
    )


def test_wvfm_scale():
    wf = Linear(start=1.0, stop=2.0, duration=3.0)
    wf2 = 2.0 * wf

    assert wf2.print_node() == "Scale"
    assert wf2.children() == [cast(2.0), wf]
    assert isinstance(hash(wf), int)

    assert wf2.eval_decimal(Decimal("0.0")) == Decimal("2.0")

    wf3 = wf * 2.0
    assert wf3.print_node() == "Scale"
    assert wf3.children() == [cast(2.0), wf]

    assert wf3.eval_decimal(Decimal("3.0")) == Decimal("4.0")

    mystdout = StringIO()
    p = PP(mystdout)

    wf3._repr_pretty_(p, 2)

    assert (
        mystdout.getvalue()
        == "Scale\n"
        + "├─ Literal: 2.0\n"
        + "└─ Linear\n"
        + "   ├─ start\n"
        + "   │  ⇒ Literal: 1.0\n"
        + "   ├─ stop\n"
        + "   │  ⇒ Literal: 2.0\n"
        + "   └─ duration\n"
        + "      ⇒ Literal: 3.0"
    )


def test_wvfn_add():
    wf = Constant(value=1.0, duration=3.0)
    wf2 = Linear(start=1.0, stop=2.0, duration=2.0)

    wf3 = wf + wf2

    assert wf3.print_node() == "+"
    assert wf3.children() == [wf, wf2]
    assert isinstance(hash(wf), int)

    assert wf3.eval_decimal(Decimal("0")) == Decimal("2.0")
    assert wf3.eval_decimal(Decimal("2.5")) == Decimal("1.0")

    mystdout = StringIO()
    p = PP(mystdout)

    wf3._repr_pretty_(p, 2)

    assert (
        mystdout.getvalue()
        == "+\n"
        + "├─ Constant\n"
        + "│  ├─ value\n"
        + "│  │  ⇒ Literal: 1.0\n"
        + "│  └─ duration\n"
        + "│     ⇒ Literal: 3.0\n"
        + "└─ Linear\n"
        + "   ├─ start\n"
        + "   │  ⇒ Literal: 1.0\n"
        + "   ├─ stop\n"
        + "   │  ⇒ Literal: 2.0\n"
        + "   └─ duration\n"
        + "      ⇒ Literal: 2.0"
    )


def test_wvfn_rec():
    wf = Linear(start=1.0, stop=2.0, duration=3.0)

    re = Record(wf, cast("tst"))

    assert re.print_node() == "Record"
    assert re.children() == {"Waveform": wf, "Variable": cast("tst")}
    assert isinstance(hash(wf), int)

    assert re.eval_decimal(Decimal("0")) == Decimal("1.0")
    assert re.duration == cast(3.0)

    mystdout = StringIO()
    p = PP(mystdout)

    re._repr_pretty_(p, 2)

    assert (
        mystdout.getvalue()
        == "Record\n"
        + "├─ Waveform\n"
        + "│  ⇒ Linear\n"
        + "│    ├─ start\n"
        + "│    │  ⇒ Literal: 1.0\n"
        + "│    ├─ stop\n"
        + "│    │  ⇒ Literal: 2.0\n"
        + "│    └─ duration\n"
        + "│       ⇒ Literal: 3.0\n"
        + "└─ Variable\n"
        + "   ⇒ Variable: tst"
    )


def test_wvfn_poly():
    wf = Poly(coeffs=[cast(1), cast(2), cast(3)], duration=10)

    assert wf.print_node() == "Poly"
    assert wf.children() == {
        "b": wf.coeffs[0],
        "t": wf.coeffs[1],
        "t^2": wf.coeffs[2],
        "duration": cast(10),
    }
    assert wf.eval_decimal(Decimal("0.5")) == (1) + (2) * 0.5 + (3) * 0.5**2
    assert wf.eval_decimal(Decimal("20")) == Decimal("0")
    assert isinstance(hash(wf), int)


def test_align():
    wf = Linear(start=1.0, stop=2.0, duration=3.0)
    wf1 = wf.align(Alignment.Left)
    wf2 = wf.align(Alignment.Right, 0.0)
    wf3 = wf.align(Alignment.Right)

    assert wf.align(Alignment.Right, Side.Left) == AlignedWaveform(
        wf, Alignment.Right, Side.Left
    )
    assert wf1.print_node() == "AlignedWaveform"
    assert wf1.children() == {"Waveform": wf, "Alignment": "Left", "Value": "Right"}
    assert wf2.children() == {"Waveform": wf, "Alignment": "Right", "Value": cast(0.0)}
    assert wf3.children() == {"Waveform": wf, "Alignment": "Right", "Value": "Left"}
    with pytest.raises(ValueError):
        wf1.align(Alignment.Right, Side.Right)


##-----------------------------


def test_dunders():
    class MyNewType:
        def __init__(self, value) -> None:
            self.value = value

        def __radd__(self, other: Waveform):
            return Constant(self.value, other.duration) + other

        def __rsub__(self, other: Waveform):
            return Constant(self.value, other.duration) - other

    obj = MyNewType(2)
    assert Constant(2, 1) + obj == 2 * Constant(2, 1)
    assert Constant(2, 1) - obj == Constant(2, 1) - Constant(2, 1)
    assert Constant(2, 1) / 2 == 0.5 * Constant(2, 1)


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

    assert wf.eval_decimal(Decimal("0.1")) == 1.0844831620655968


def test_wvfn_slice():
    iv = Interval(cast(0), cast(0.3))
    wv = Constant(value=2.0, duration=3.0)

    wf = Slice(wv, iv)

    assert wf.print_node() == "Slice"
    assert wf.eval_decimal(Decimal("0.4")) == 0
    assert wf.eval_decimal(Decimal("0.2")) == 2.0
    assert wf.children() == [iv, wv]
    assert isinstance(hash(wf), int)

    mystdout = StringIO()
    p = PP(mystdout)
    wf._repr_pretty_(p, 2)

    assert (
        mystdout.getvalue()
        == "Slice\n"
        + "├─ Interval\n"
        + "│  ├─ start\n"
        + "│  │  ⇒ Literal: 0\n"
        + "│  └─ stop\n"
        + "│     ⇒ Literal: 0.3\n"
        + "└─ Constant\n"
        + "   ├─ value\n"
        + "   │  ⇒ Literal: 2.0\n"
        + "   └─ duration\n"
        + "      ⇒ Literal: 3.0"
    )

    iv_err1 = Interval(None, None)
    wf2 = Slice(wv, iv_err1)
    with pytest.raises(ValueError):
        wf2.duration

    iv2 = Interval(cast(0), None)
    wf3 = Slice(wv, iv2)

    assert wf3.duration() == Decimal("3.0")


def test_wvfm_align():
    wv = Constant(value=2.0, duration=3.0)

    wf = AlignedWaveform(wv, Alignment.Left, cast(0.2))
    assert wf.print_node() == "AlignedWaveform"
    assert wf.children() == {"Waveform": wv, "Alignment": "Left", "Value": cast(0.2)}
    assert isinstance(hash(wf), int)

    wf2 = AlignedWaveform(wv, Alignment.Left, Side.Right)
    assert wf2.print_node() == "AlignedWaveform"
    assert wf2.children() == {"Waveform": wv, "Alignment": "Left", "Value": "Right"}

    wf3 = AlignedWaveform(wv, Alignment.Right, Side.Left)
    assert wf3.print_node() == "AlignedWaveform"
    assert wf3.children() == {"Waveform": wv, "Alignment": "Right", "Value": "Left"}

    mystdout = StringIO()
    p = PP(mystdout)
    wf3._repr_pretty_(p, 2)

    assert (
        mystdout.getvalue()
        == "AlignedWaveform\n"
        + "├─ Waveform\n"
        + "│  ⇒ Constant\n"
        + "│    ├─ value\n"
        + "│    │  ⇒ Literal: 2.0\n"
        + "│    └─ duration\n"
        + "│       ⇒ Literal: 3.0\n"
        + "├─ Alignment\n"
        + "│  ⇒ Right\n"
        + "└─ Value\n"
        + "   ⇒ Left\n"
    )


def test_wvfm_sample():
    def my_cos(time):
        return np.cos(time)

    assert my_cos(1) == np.cos(1)

    wv = PythonFn.create(my_cos, duration=1.0)
    dt = cast(0.1)

    wf = Sample(wv, Interpolation.Constant, dt)

    assert wf.print_node() == "Sample constant"
    assert wf.children() == {"Waveform": wv, "sample_step": dt}
    assert wf.eval_decimal(Decimal(0.05)) == my_cos(0)
    assert float(wf.eval_decimal(Decimal(0))) == my_cos(0)
    assert isinstance(hash(wf), int)

    wf2 = Sample(wv, Interpolation.Linear, dt)

    assert wf2.print_node() == "Sample linear"
    assert wf2.children() == {"Waveform": wv, "sample_step": dt}
    slope = (my_cos(0.1) - my_cos(0)) / 0.1
    assert float(wf2.eval_decimal(Decimal(0.05))) == float(my_cos(0) + slope * 0.05)
    assert float(wf2.eval_decimal(Decimal(3))) == 0
    assert float(wf2.eval_decimal(Decimal(0))) == my_cos(0)
    assert isinstance(hash(wf), int)

    mystdout = StringIO()
    p = PP(mystdout)

    wf2._repr_pretty_(p, 2)

    assert (
        mystdout.getvalue()
        == "Sample linear\n"
        + "├─ Waveform\n"
        + "│  ⇒ PythonFn: my_cos\n"
        + "│    └─ duration\n"
        + "│       ⇒ Literal: 1.0\n"
        + "└─ sample_step\n"
        + "   ⇒ Literal: 0.1"
    )


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
