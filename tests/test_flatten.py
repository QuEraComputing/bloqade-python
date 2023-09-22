from bloqade import start, var
import pytest


def test_options_1():
    def detuning(t, x, y):
        return y * t + x

    program = (
        start.add_position((0, 0))
        .add_position((0, "d"))
        .rydberg.rabi.amplitude.uniform.fn(detuning, 4)
        .sample(0.05)
        .assign(x=1)
        .batch_assign(d=[0, 1])
        .flatten([var("y")])
        .parallelize(20)
        .quera.mock()
    )

    results = program.run(100, args=(2,)).report().counts

    assert isinstance(results, list)


def test_options_2():
    def detuning(t, x, y):
        return y * t + x

    program = (
        start.add_position((0, 0))
        .add_position((0, "d"))
        .rydberg.rabi.amplitude.uniform.fn(detuning, 4)
        .sample(0.05)
        .assign(x=1)
        .flatten(["y", "d"])
        .parallelize(20)
        .quera.mock()
    )

    results = program.run(100, args=(2, 4)).report().counts

    assert isinstance(results, list)


def test_options_3():
    def detuning(t, x, y):
        return y * t + x

    program = (
        start.add_position((0, 0))
        .add_position((0, "d"))
        .rydberg.rabi.amplitude.uniform.fn(detuning, 4)
        .sample(0.05)
        .assign(x=1)
        .batch_assign(d=[0, 1], y=[0, 1])
        .parallelize(20)
        .quera.mock()
    )

    results = program.run(100).report().counts

    assert isinstance(results, list)


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

    results = program.run(100).report().counts

    assert isinstance(results, list)

    with pytest.raises(ValueError):
        # checking that using `arg` is not allowed without flatten
        program.run(100, args=(2,))
