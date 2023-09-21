from bloqade import start, var
from bloqade.atom_arrangement import Chain
from bloqade.serialize import dumps, loads
import numpy as np
from beartype.typing import Dict


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
        .run(10000, cache_matrices=True, blockade_radius=6.0, interaction_picture=True)
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


def test_integration_5():
    ramp_time = var("ramp_time")
    (
        start.add_position((0, 0))
        .add_position((0, 5.0))
        .scale("r")
        .rydberg.detuning.uniform.piecewise_linear(
            [0.1, ramp_time, 0.1], [-100, -100, 100, 100]
        )
        .amplitude.uniform.piecewise_linear([0.1, ramp_time, 0.1], [0, 10, 10, 0])
        .phase.location(1)
        .linear(0.0, 1.0, ramp_time + 0.2)
        .assign(ramp_time=3.0)
        .batch_assign(r=np.linspace(4, 10, 11).tolist())
        .bloqade.python()
        .run(10000, cache_matrices=True, blockade_radius=6.0)
        .report()
        .bitstrings()
    )


def test_integration_6():
    ramp_time = var("ramp_time")
    (
        start.add_position((0, 0))
        .add_position((0, 5.0))
        .scale("r")
        .rydberg.detuning.uniform.piecewise_linear(
            [0.1, ramp_time, 0.1], [-100, -100, 100, 100]
        )
        .location(1)
        .constant(3.0, ramp_time + 0.2)
        .location(0)
        .linear(2.0, 0, ramp_time + 0.2)
        .amplitude.uniform.piecewise_linear([0.1, ramp_time, 0.1], [0, 10, 10, 0])
        .phase.location(1)
        .linear(0.0, 1.0, ramp_time + 0.2)
        .assign(ramp_time=3.0)
        .batch_assign(r=np.linspace(4, 10, 11).tolist())
        .bloqade.python()
        .run(10000, cache_matrices=True, blockade_radius=6.0)
        .report()
        .bitstrings()
    )


def test_serialization():
    ramp_time = var("ramp_time")
    batch = (
        start.add_position((0, 0))
        .add_position((0, 5.0))
        .scale("r")
        .rydberg.detuning.uniform.piecewise_linear(
            [0.1, ramp_time, 0.1], [-100, -100, 100, 100]
        )
        .amplitude.uniform.piecewise_linear([0.1, ramp_time, 0.1], [0, 10, 10, 0])
        .amplitude.var("rabi_mask")
        .piecewise_linear([0.1, ramp_time, 0.1], [0, 10, 10, 0])
        .amplitude.location(1)
        .linear(0.0, 1.0, ramp_time + 0.2)
        .assign(ramp_time=3.0, rabi_mask=[10.0, 0.1])
        .batch_assign(r=np.linspace(4, 10, 11).tolist())
        .bloqade.python()
        ._compile(100)
    )

    obj_str = dumps(batch)
    batch2 = loads(obj_str)
    assert isinstance(batch2, type(batch))


def KS_test(
    lhs_counts: Dict[str, int], rhs_counts: Dict[str, int], alpha: float = 0.05
) -> None:
    # statistical test to check of two empirical distributions are the same
    # https://en.wikipedia.org/wiki/Kolmogorov%E2%80%93Smirnov_test#Two-sample_Kolmogorov%E2%80%93Smirnov_test
    m = sum(lhs_counts.values())
    n = sum(rhs_counts.values())
    lhs_cdf = []
    rhs_cdf = []
    bitstrings = sorted(list(set([*lhs_counts.keys(), *rhs_counts.keys()])))
    for bitstring in bitstrings:
        lhs_cdf.append(lhs_counts.get(bitstring, 0) / n)
        rhs_cdf.append(rhs_counts.get(bitstring, 0) / m)

    lhs_cdf = np.cumsum(lhs_cdf)
    rhs_cdf = np.cumsum(rhs_cdf)

    c_alpha = np.sqrt(-0.5 * np.log(alpha / 2))

    assert np.linalg.norm(lhs_cdf - rhs_cdf, ord=np.inf) <= c_alpha * np.sqrt(
        (m + n) / (m * n)
    )


def test_bloqade_against_braket():
    prog = (
        Chain(5, lattice_spacing=6.1)
        .rydberg.detuning.uniform.piecewise_linear(
            [0.1, 3.0, 0.1], [-20, -20, "d", "d"]
        )
        .amplitude.uniform.piecewise_linear([0.1, 3.0, 0.1], [0, 15, 15, 0])
        .phase.uniform.constant(0.3, 3.2)
        .batch_assign(d=[0, 10, 20, 30, 40])
    )

    nshots = 1000
    a = prog.bloqade.python().run(nshots, cache_matrices=True).report().counts
    b = prog.braket.local_emulator().run(nshots).report().counts

    for lhs, rhs in zip(a, b):
        KS_test(lhs, rhs)
