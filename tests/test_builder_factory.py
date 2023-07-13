from bloqade.builder.factory import (
    piecewise_linear,
    piecewise_constant,
    constant,
    linear,
)
from bloqade import cast


def test_ir_piecewise_linear():
    A = piecewise_linear([0.1, 3.8, 0.2], [-10, -7, "a", "b"])

    ## Append type ir node
    assert len(A.waveforms) == 3
    assert A.waveforms[0].duration == cast(0.1)
    assert A.waveforms[0].start == cast(-10)
    assert A.waveforms[0].stop == cast(-7)

    assert A.waveforms[1].duration == cast(3.8)
    assert A.waveforms[1].start == cast(-7)
    assert A.waveforms[1].stop == cast("a")

    assert A.waveforms[2].duration == cast(0.2)
    assert A.waveforms[2].start == cast("a")
    assert A.waveforms[2].stop == cast("b")


def test_ir_const():
    A = constant(value=3.415, duration=0.55)

    ## Constant type ir node:
    assert A.value == cast(3.415)
    assert A.duration == cast(0.55)


def test_ir_linear():
    A = linear(start=0.5, stop=3.2, duration=0.76)

    ## Linear type ir node:
    assert A.start == cast(0.5)
    assert A.stop == cast(3.2)
    assert A.duration == cast(0.76)


def test_ir_piecewise_constant():
    A = piecewise_constant(durations=[0.1, 3.8, 0.2], values=[-10, "a", "b"])

    assert A.waveforms[0].duration == cast(0.1)
    assert A.waveforms[0].value == cast(-10)

    assert A.waveforms[1].duration == cast(3.8)
    assert A.waveforms[1].value == cast("a")

    assert A.waveforms[2].duration == cast(0.2)
    assert A.waveforms[2].value == cast("b")
