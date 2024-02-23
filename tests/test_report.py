from collections import OrderedDict
from decimal import Decimal
from bloqade.ir.location import ListOfLocations
import tempfile
import pandas as pd
import numpy as np
from bloqade.task.base import Report, Geometry


def test_integration_report():
    prog = (
        ListOfLocations()
        .add_position((0, 0))
        .add_position((0, 6))
        .add_position((0, 3))
        .rydberg.detuning.uniform.piecewise_linear(
            durations=["up_time", "anneal_time", "up_time"],
            values=[
                "initial_detuning",
                "initial_detuning",
                "final_detuning",
                "final_detuning",
            ],
        )
        .rydberg.rabi.amplitude.uniform.piecewise_linear(
            durations=["up_time", "anneal_time", "up_time"],
            values=[0, "rabi_amplitude_max", "rabi_amplitude_max", 0],
        )
        .assign(
            up_time=0.1,
            anneal_time=3.8,
            initial_detuning=-15,
            final_detuning=10,
            rabi_amplitude_max=15,
        )
    )

    with tempfile.NamedTemporaryFile() as f:
        future = prog.quera.mock(state_file=f.name).run_async(shots=100)
        future.pull()
        future2 = future.remove_tasks("Completed")
        future2

    report = future.report()

    bistrings = report.bitstrings()
    counts = report.counts()
    dataframe = report.dataframe
    rydberg_densities = report.rydberg_densities()

    print(bistrings)
    print(counts)
    print(dataframe)
    print(rydberg_densities)


def get_report():
    data = [
        ((0, (0, 0), "11", "11"), np.asarray([1, 1], dtype=np.uint8)),
        ((0, (0, 0), "11", "11"), np.asarray([0, 0], dtype=np.uint8)),
        ((0, (1, 0), "11", "11"), np.asarray([1, 0], dtype=np.uint8)),
        ((0, (1, 0), "11", "11"), np.asarray([1, 0], dtype=np.uint8)),
        ((1, (0, 0), "11", "11"), np.asarray([1, 1], dtype=np.uint8)),
        ((1, (0, 0), "11", "11"), np.asarray([0, 1], dtype=np.uint8)),
        ((1, (1, 0), "11", "10"), np.asarray([1, 0], dtype=np.uint8)),
        ((1, (1, 0), "11", "11"), np.asarray([1, 1], dtype=np.uint8)),
    ]

    metas = [dict(a=1, c=[1, 2]), dict(a=2, b=3, c=[1, 4])]
    geos = [
        Geometry([(0, 0), (0, 6)], [1, 1], None),
        Geometry([(0, 0), (0, 6)], [1, 1], None),
    ]

    index, bitstrings = list(zip(*data))

    index = pd.MultiIndex.from_tuples(
        index, names=["task_number", "cluster", "perfect_sorting", "pre_sequence"]
    )

    dataframe = pd.DataFrame(bitstrings, index=index)

    return Report(dataframe, metas, geos)


def test_list_param():
    report = get_report()

    assert report.list_param("a") == [Decimal("1"), Decimal("2")], "failed, a"
    assert report.list_param("b") == [None, Decimal("3")], "failed, b"
    assert report.list_param("c") == [
        [Decimal("1"), Decimal("2")],
        [Decimal("1"), Decimal("4")],
    ], "failed, c"


def test_bitstrings():
    report = get_report()

    expected_bitstrings = [
        np.array([[1, 1], [0, 0], [1, 0], [1, 0]], dtype=np.uint8),
        np.array([[1, 1], [0, 1], [1, 0], [1, 1]], dtype=np.uint8),
    ]

    bitstrings = report.bitstrings(filter_perfect_filling=False)

    assert all(
        np.equal(lhs, rhs).all() for lhs, rhs in zip(bitstrings, expected_bitstrings)
    ), "failed, no filter"

    expected_bitstrings = [
        np.array([[1, 1], [0, 0], [1, 0], [1, 0]], dtype=np.uint8),
        np.array([[1, 1], [0, 1], [1, 1]], dtype=np.uint8),
    ]

    bitstrings = report.bitstrings(filter_perfect_filling=True)

    assert all(
        np.equal(lhs, rhs).all() for lhs, rhs in zip(bitstrings, expected_bitstrings)
    ), "failed, filter perfect filling"

    expected_bitstrings = [
        np.asarray([[1, 1], [0, 0]], dtype=np.uint8),
        np.asarray([[1, 1], [0, 1]], dtype=np.uint8),
    ]

    bitstrings = report.bitstrings(filter_perfect_filling=True, clusters=(0, 0))

    assert all(
        np.equal(lhs, rhs).all() for lhs, rhs in zip(bitstrings, expected_bitstrings)
    ), "failed, filter perfect filling and cluster (0, 0)"

    expected_bitstrings = [
        np.asarray([[1, 0], [1, 0]], dtype=np.uint8),
        np.asarray([[1, 1]], dtype=np.uint8),
    ]

    bitstrings = report.bitstrings(filter_perfect_filling=True, clusters=(1, 0))

    assert all(
        np.equal(lhs, rhs).all() for lhs, rhs in zip(bitstrings, expected_bitstrings)
    ), "failed, filter perfect filling and cluster (1, 0))"


def test_counts():
    report = get_report()

    counts_0 = OrderedDict()
    counts_1 = OrderedDict()

    counts_0["10"] = 2
    counts_0["00"] = 1
    counts_0["11"] = 1

    counts_1["11"] = 2
    counts_1["01"] = 1
    counts_1["10"] = 1

    expected_counts = [
        counts_0,
        counts_1,
    ]

    counts = report.counts(filter_perfect_filling=False)

    assert counts == expected_counts, "failed, no filter"

    counts_0 = OrderedDict()
    counts_1 = OrderedDict()

    counts_0["10"] = 2
    counts_0["00"] = 1
    counts_0["11"] = 1

    counts_1["11"] = 2
    counts_1["01"] = 1

    expected_counts = [
        counts_0,
        counts_1,
    ]

    counts = report.counts(filter_perfect_filling=True)

    assert counts == expected_counts, "failed, filter perfect filling"

    counts_0 = OrderedDict()
    counts_1 = OrderedDict()

    counts_0["00"] = 1
    counts_0["11"] = 1

    counts_1["01"] = 1
    counts_1["11"] = 1

    expected_counts = [
        counts_0,
        counts_1,
    ]

    counts = report.counts(filter_perfect_filling=True, clusters=(0, 0))

    assert (
        counts == expected_counts
    ), "failed, filter perfect filling and cluster (0, 0)"

    counts_0 = OrderedDict()
    counts_1 = OrderedDict()

    counts_0["10"] = 2

    counts_1["11"] = 1

    expected_counts = [
        counts_0,
        counts_1,
    ]

    counts = report.counts(filter_perfect_filling=True, clusters=(1, 0))

    assert (
        counts == expected_counts
    ), "failed, filter perfect filling and cluster (1, 0)"


def test_rydberg_densities():
    report = get_report()

    index = pd.MultiIndex.from_tuples([(0,), (1,)], names=["task_number"])

    expected_rydberg_densities = [
        np.array([0.25, 0.75]),
        np.array([0.25, 0.25]),
    ]

    expected_rydberg_densities = pd.DataFrame(expected_rydberg_densities, index=index)

    assert np.array_equal(
        expected_rydberg_densities.to_numpy(),
        report.rydberg_densities(filter_perfect_filling=False).to_numpy(),
    ), "failed, no filter"

    expected_rydberg_densities = [
        np.array([0.25, 0.75]),
        np.array([0.3333333, 0.0]),
    ]

    expected_rydberg_densities = pd.DataFrame(expected_rydberg_densities, index=index)

    assert np.allclose(
        expected_rydberg_densities.to_numpy(),
        report.rydberg_densities(filter_perfect_filling=True).to_numpy(),
    ), "failed, filter perfect filling"

    expected_rydberg_densities = [
        np.array([0.5, 0.5]),
        np.array([0.5, 0.0]),
    ]

    expected_rydberg_densities = pd.DataFrame(expected_rydberg_densities, index=index)

    assert np.array_equal(
        expected_rydberg_densities.to_numpy(),
        report.rydberg_densities(
            filter_perfect_filling=True, clusters=(0, 0)
        ).to_numpy(),
    ), "failed, filter perfect filling and cluster (0, 0)"

    expected_rydberg_densities = [
        np.array([0.0, 1.0]),
        np.array([0.0, 0.0]),
    ]

    expected_rydberg_densities = pd.DataFrame(expected_rydberg_densities, index=index)

    assert np.array_equal(
        expected_rydberg_densities.to_numpy(),
        report.rydberg_densities(
            filter_perfect_filling=True, clusters=(1, 0)
        ).to_numpy(),
    ), "failed, filter perfect filling and cluster (1, 0)"
