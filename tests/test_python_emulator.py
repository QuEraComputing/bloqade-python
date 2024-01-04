from bloqade import start, var, cast, dumps, loads
from bloqade.atom_arrangement import Chain
import numpy as np
from beartype.typing import Dict
from scipy.stats import ks_2samp


def test_integration_1():
    batch = (
        start.add_position((0, 0))
        .add_position((0, 5.0))
        .scale("r")
        .rydberg.detuning.uniform.piecewise_linear(
            [0.1, "ramp_time", 0.1], [-100, -100, 100, 100]
        )
        .amplitude.uniform.piecewise_linear([0.1, "ramp_time", 0.1], [0, 10, 10, 0])
        .assign(ramp_time=3.0, r=8)
        .bloqade.python()
        .run(10000, cache_matrices=True, blockade_radius=6.0, interaction_picture=True)
    )

    batch_str = dumps(batch)
    batch2 = loads(batch_str)
    assert isinstance(batch2, type(batch))
    batch2.report().bitstrings()


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
        .assign(ramp_time=3.0, r=6)
        .bloqade.python()
        .run(10000, cache_matrices=False, blockade_radius=6.0, multiprocessing=False)
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
        .amplitude.scale("rabi_mask")
        .fn(lambda t: 4 * np.sin(3 * t), ramp_time + 0.2)
        .assign(ramp_time=3.0, rabi_mask=[10.0, 0.1], r=6)
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
        .amplitude.scale("rabi_mask")
        .fn(lambda t: 4 * np.sin(3 * t), ramp_time + 0.2)
        .amplitude.location(1)
        .linear(0.0, 1.0, ramp_time + 0.2)
        .assign(ramp_time=3.0, rabi_mask=[10.0, 0.1], r=6)
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
        .assign(ramp_time=3.0, r=6)
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
        .assign(ramp_time=3.0, r=6)
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
        .amplitude.scale("rabi_mask")
        .piecewise_linear([0.1, ramp_time, 0.1], [0, 10, 10, 0])
        .amplitude.location(1)
        .linear(0.0, 1.0, ramp_time + 0.2)
        .assign(ramp_time=3.0, rabi_mask=[10.0, 0.1])
        .batch_assign(r=np.linspace(0.1, 4, 5).tolist())
        .bloqade.python()
        ._compile(100)
    )

    obj_str = dumps(batch)
    batch2 = loads(obj_str)
    assert isinstance(batch2, type(batch))


def KS_test(
    lhs_counts: Dict[str, int], rhs_counts: Dict[str, int], alpha: float = 0.05
) -> None:
    lhs_samples = []
    rhs_samples = []

    for bitstring, count in lhs_counts.items():
        lhs_samples += [int(bitstring, 2)] * count

    for bitstring, count in rhs_counts.items():
        rhs_samples += [int(bitstring, 2)] * count

    result = ks_2samp(lhs_samples, rhs_samples, method="exact")

    assert result.pvalue > alpha


def test_bloqade_against_braket():
    np.random.seed(9123892)
    durations = cast([0.1, 0.1, 0.1])

    prog = (
        Chain(3, lattice_spacing=6.1)
        .rydberg.detuning.uniform.piecewise_linear(durations, [-20, -20, "d", "d"])
        .amplitude.uniform.piecewise_linear(durations, [0, 15, 15, 0])
        .phase.uniform.constant(0.3, sum(durations))
        .batch_assign(d=[10, 20])
    )

    nshots = 1000
    a = prog.bloqade.python().run(nshots, cache_matrices=True).report().counts()
    b = prog.braket.local_emulator().run(nshots).report().counts()

    for lhs, rhs in zip(a, b):
        KS_test(lhs, rhs)


def test_bloqade_against_braket_2():
    np.random.seed(192839812)
    durations = cast([0.1, 0.1, 0.1])
    values = [0, 15, 15, 0]

    prog_1 = (
        Chain(3, lattice_spacing=6.1)
        .rydberg.detuning.uniform.piecewise_linear(durations, [-20, -20, "d", "d"])
        .amplitude.uniform.piecewise_linear(durations, values)
        .batch_assign(d=[10, 20])
    )
    prog_2 = (
        Chain(3, lattice_spacing=6.1)
        .rydberg.detuning.uniform.piecewise_linear(durations, [-20, -20, "d", "d"])
        .amplitude.location(0)
        .piecewise_linear(durations, values)
        .amplitude.location(1)
        .piecewise_linear(durations, values)
        .amplitude.location(2)
        .piecewise_linear(durations, values)
        .phase.location(0)
        .constant(0.0, sum(durations))
        .batch_assign(d=[10, 20])
    )

    nshots = 1000
    a = prog_2.bloqade.python().run(nshots, cache_matrices=True).report().counts()
    b = prog_1.braket.local_emulator().run(nshots).report().counts()

    for lhs, rhs in zip(a, b):
        KS_test(lhs, rhs)
