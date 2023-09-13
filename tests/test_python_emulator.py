from bloqade import start, var
import numpy as np


def test_integration_1():
    (
        start.add_position((0, 0))
        .add_position((0, 5.0))
        .scale("r")
        .rydberg.detuning.uniform.piecewise_linear(
            [0.1, "ramp_time", 0.1], [-100, -100, 100, 100]
        )
        .amplitude.uniform.piecewise_linear([0.1, "ramp_time", 0.1], [0, 10, 10, 0])
        .assign(ramp_time=3.0)
        .batch_assign(r=np.linspace(4, 10, 11).tolist())
        .bloqade.python()
        .run(10000, cache_matrices=True, blockade_radius=6.0)
        .report()
        .bitstrings()
    )


def test_integration_2():
    ramp_time = var("ramp_time")
    (
        start.add_position((0, 0))
        .add_position((0, 5.0))
        .scale("r")
        .rydberg.detuning.uniform.piecewise_linear(
            [0.1, "ramp_time", 0.1], [-100, -100, 100, 100]
        )
        .amplitude.uniform.piecewise_linear([0.1, ramp_time, 0.1], [0, 10, 10, 0])
        .phase.uniform.piecewise_constant(
            [0.1, ramp_time / 2, ramp_time / 2, 0.1], [0, 0, np.pi, np.pi]
        )
        .assign(ramp_time=3.0)
        .batch_assign(r=np.linspace(4, 10, 11).tolist())
        .bloqade.python()
        .run(10000, cache_matrices=True, blockade_radius=6.0)
        .report()
        .bitstrings()
    )


def test_integration_3():
    ramp_time = var("ramp_time")
    (
        start.add_position((0, 0))
        .add_position((0, 5.0))
        .scale("r")
        .rydberg.detuning.uniform.piecewise_linear(
            [0.1, ramp_time, 0.1], [-100, -100, 100, 100]
        )
        .amplitude.uniform.piecewise_linear([0.1, ramp_time, 0.1], [0, 10, 10, 0])
        .phase.uniform.piecewise_constant(
            [0.1, ramp_time / 2, ramp_time / 2, 0.1], [0, 0, np.pi, np.pi]
        )
        .amplitude.var("rabi_mask")
        .fn(lambda t: 4 * np.sin(3 * t), ramp_time + 0.2)
        .assign(ramp_time=3.0, rabi_mask=[10.0, 0.1])
        .batch_assign(r=np.linspace(4, 10, 11).tolist())
        .bloqade.python()
        .run(10000, cache_matrices=True, blockade_radius=6.0)
        .report()
        .bitstrings()
    )


def test_integration_4():
    ramp_time = var("ramp_time")
    (
        start.add_position((0, 0))
        .add_position((0, 5.0))
        .scale("r")
        .rydberg.detuning.uniform.piecewise_linear(
            [0.1, ramp_time, 0.1], [-100, -100, 100, 100]
        )
        .amplitude.uniform.piecewise_linear([0.1, ramp_time, 0.1], [0, 10, 10, 0])
        .amplitude.var("rabi_mask")
        .fn(lambda t: 4 * np.sin(3 * t), ramp_time + 0.2)
        .amplitude.location(1)
        .linear(0.0, 1.0, ramp_time + 0.2)
        .assign(ramp_time=3.0, rabi_mask=[10.0, 0.1])
        .batch_assign(r=np.linspace(4, 10, 11).tolist())
        .bloqade.python()
        .run(10000, cache_matrices=True, blockade_radius=6.0)
        .report()
        .bitstrings()
    )
