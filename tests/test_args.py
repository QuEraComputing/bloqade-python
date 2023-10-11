from bloqade import start, var
import pytest


def test_options_1():
    def detuning(t, x, y):
        return y * t + x

    (
        start.add_position((0, 0))
        .add_position((0, "d"))
        .rydberg.rabi.amplitude.uniform.fn(detuning, 4)
        .sample(0.05)
        .assign(x=1)
        .batch_assign(d=[0, 1])
        .args([var("y")])
        .parallelize(20)
        .quera.mock()
        ._compile(100, args=(2,))
    )


def test_options_2():
    def detuning(t, x, y):
        return y * t + x

    (
        start.add_position((0, 0))
        .add_position((0, "d"))
        .rydberg.rabi.amplitude.uniform.fn(detuning, 4)
        .sample(0.05)
        .assign(x=1)
        .args(["y", "d"])
        .parallelize(20)
        .quera.mock()
        ._compile(100, args=(2, 4))
    )


def test_options_3():
    def detuning(t, x, y):
        return y * t + x

    (
        start.add_position((0, 0))
        .add_position((0, "d"))
        .rydberg.rabi.amplitude.uniform.fn(detuning, 4)
        .sample(0.05)
        .assign(x=1)
        .batch_assign(d=[0, 1], y=[0, 1])
        .parallelize(20)
        .quera.mock()
        ._compile(100)
    )


def test_options_4():
    def detuning(t, x, y):
        return y * t + x

    program = (
        start.add_position((0, 0))
        .add_position((0, "d"))
        .rydberg.rabi.amplitude.uniform.fn(detuning, 4)
        .sample(0.05)
        .assign(x=1)
        .batch_assign(d=[0, 1], y=[0, 1])
        .quera.mock()
    )

    program._compile(100)

    with pytest.raises(ValueError):
        # checking that using `arg` is not allowed without args
        program._compile(100, args=(2,))


def test_options_5():
    def detuning(t, x, y):
        return y * t + x

    (
        start.add_position((0, 0))
        .add_position((0, 6.1))
        .add_position((0, "d"))
        .rydberg.detuning.scale("mask")
        .fn(detuning, 4)
        .sample(0.05)
        .assign(x=1)
        .batch_assign(d=[0, 1], y=[0, 1])
        .args(["mask"])
        .parallelize(20)
        .quera.mock()
        ._compile(100, args=(0, 1, 0))
    )

    with pytest.raises(ValueError):
        (
            start.add_position((0, 0))
            .add_position((0, 6.1))
            .add_position((0, "d"))
            .rydberg.detuning.scale("mask")
            .fn(detuning, 4)
            .sample(0.05)
            .assign(x=1)
            .batch_assign(d=[0, 1], y=[0, 1])
            .args(["mask"])
            .parallelize(20)
            .quera.mock()
            ._compile(100, args=(0, 0.5))
        )
