# from bloqade import start
from bloqade.ir import location
from bloqade.ir import Constant, Linear, Poly
import pytest
import json
import numpy as np


def test_integration_jump_err():
    ## jump at the end of linear -- constant
    with pytest.raises(ValueError):
        (
            location.Square(6)
            .rydberg.detuning.uniform.apply(
                Constant("initial_detuning", "up_time")
                .append(Linear("initial_detuning", "final_detuning", "anneal_time"))
                .append(0.5 * Constant("final_detuning", "up_time"))
            )
            .assign(
                initial_detuning=-10,
                up_time=0.1,
                final_detuning=15,
                anneal_time=10,
            )
            .mock(10)
        )


def test_integration_scale():
    seq = Linear(start=0.0, stop=1.0, duration=0.5).append(
        2 * Constant(0.5, duration=0.5)
    )
    job = location.Square(1).rydberg.detuning.uniform.apply(seq).mock(10)

    panel = json.loads(job.json())

    print(panel)

    ir = panel["tasks"]["0"]["task_ir"]

    assert ir["nshots"] == 10
    assert ir["lattice"]["sites"][0] == [0.0, 0.0]
    assert ir["lattice"]["filling"] == [1]
    assert ir["lattice"]["filling"] == [1]

    detune_ir = ir["effective_hamiltonian"]["rydberg"]["detuning"]
    assert all(detune_ir["global"]["times"] == np.array([0, 0.5, 1.0]) * 1e-6)
    assert all(detune_ir["global"]["values"] == np.array([0, 1, 1]) * 1e6)


def test_integration_neg():
    seq = Linear(start=0.0, stop=-0.5, duration=0.5).append(
        -Constant(0.5, duration=0.5)
    )
    job = location.Square(1).rydberg.detuning.uniform.apply(seq).mock(10)

    panel = json.loads(job.json())
    print(panel)

    ir = panel["tasks"]["0"]["task_ir"]

    assert ir["nshots"] == 10
    assert ir["lattice"]["sites"][0] == [0.0, 0.0]
    assert ir["lattice"]["filling"] == [1]
    assert ir["lattice"]["filling"] == [1]

    detune_ir = ir["effective_hamiltonian"]["rydberg"]["detuning"]
    assert all(detune_ir["global"]["times"] == np.array([0, 0.5, 1.0]) * 1e-6)
    assert all(detune_ir["global"]["values"] == np.array([0, -0.5, -0.5]) * 1e6)


def test_integration_poly_order_err():
    ## poly
    with pytest.raises(ValueError):
        seq = Poly(checkpoints=[1, 2, 3], duration=0.5).append(
            -Constant(0.5, duration=0.5)
        )
        (location.Square(1).rydberg.detuning.uniform.apply(seq).mock(10))


def test_integration_poly_const():
    ## constant
    seq = Poly(checkpoints=[1], duration=0.5).append(Constant(1, duration=0.5))
    job = location.Square(1).rydberg.detuning.uniform.apply(seq).mock(12)

    panel = json.loads(job.json())
    print(panel)

    ir = panel["tasks"]["0"]["task_ir"]

    assert ir["nshots"] == 12
    assert ir["lattice"]["sites"][0] == [0.0, 0.0]
    assert ir["lattice"]["filling"] == [1]
    assert ir["lattice"]["filling"] == [1]

    detune_ir = ir["effective_hamiltonian"]["rydberg"]["detuning"]
    assert all(detune_ir["global"]["times"] == np.array([0, 0.5, 1.0]) * 1e-6)
    assert all(detune_ir["global"]["values"] == np.array([1, 1, 1]) * 1e6)


def test_integration_poly_linear():
    ## linear
    seq = Poly(checkpoints=[1, 2], duration=0.5).append(Constant(2, duration=0.5))
    job = location.Square(1).rydberg.detuning.uniform.apply(seq).mock(10)

    panel = json.loads(job.json())
    print(panel)

    ir = panel["tasks"]["0"]["task_ir"]

    assert ir["nshots"] == 10
    assert ir["lattice"]["sites"][0] == [0.0, 0.0]
    assert ir["lattice"]["filling"] == [1]
    assert ir["lattice"]["filling"] == [1]

    detune_ir = ir["effective_hamiltonian"]["rydberg"]["detuning"]
    assert all(detune_ir["global"]["times"] == np.array([0, 0.5, 1.0]) * 1e-6)
    assert all(detune_ir["global"]["values"] == np.array([1, 2, 2]) * 1e6)


def test_integration_slice_linear_const():
    seq = Linear(start=0.0, stop=1.0, duration=1.0)[0:0.5].append(
        Constant(0.5, duration=0.5)
    )
    job = location.Square(1).rydberg.detuning.uniform.apply(seq).mock(10)

    panel = json.loads(job.json())

    print(panel)

    ir = panel["tasks"]["0"]["task_ir"]

    assert ir["nshots"] == 10
    assert ir["lattice"]["sites"][0] == [0.0, 0.0]
    assert ir["lattice"]["filling"] == [1]
    assert ir["lattice"]["filling"] == [1]

    detune_ir = ir["effective_hamiltonian"]["rydberg"]["detuning"]
    assert all(detune_ir["global"]["times"] == np.array([0, 0.5, 1.0]) * 1e-6)
    assert all(detune_ir["global"]["values"] == np.array([0, 0.5, 0.5]) * 1e6)


def test_integration_slice_linear_no_stop():
    seq = Linear(start=0.0, stop=1.0, duration=1.0)[0:]
    job = location.Square(1).rydberg.detuning.uniform.apply(seq).mock(10)

    panel = json.loads(job.json())

    print(panel)

    ir = panel["tasks"]["0"]["task_ir"]

    assert ir["nshots"] == 10
    assert ir["lattice"]["sites"][0] == [0.0, 0.0]
    assert ir["lattice"]["filling"] == [1]
    assert ir["lattice"]["filling"] == [1]

    detune_ir = ir["effective_hamiltonian"]["rydberg"]["detuning"]
    assert all(detune_ir["global"]["times"] == np.array([0, 1.0]) * 1e-6)
    assert all(detune_ir["global"]["values"] == np.array([0, 1.0]) * 1e6)


def test_integration_slice_linear_no_start():
    seq = Linear(start=0.0, stop=1.0, duration=1.0)[:1.0]
    job = location.Square(1).rydberg.detuning.uniform.apply(seq).mock(10)

    panel = json.loads(job.json())

    print(panel)

    ir = panel["tasks"]["0"]["task_ir"]

    assert ir["nshots"] == 10
    assert ir["lattice"]["sites"][0] == [0.0, 0.0]
    assert ir["lattice"]["filling"] == [1]
    assert ir["lattice"]["filling"] == [1]

    detune_ir = ir["effective_hamiltonian"]["rydberg"]["detuning"]
    assert all(detune_ir["global"]["times"] == np.array([0, 1.0]) * 1e-6)
    assert all(detune_ir["global"]["values"] == np.array([0, 1.0]) * 1e6)


def test_integration_slice_linear_error_neg_start():
    with pytest.raises(ValueError):
        seq = Linear(start=0.0, stop=1.0, duration=1.0)[-0.1:1.0]
        location.Square(1).rydberg.detuning.uniform.apply(seq).mock(10)


def test_integration_slice_linear_error_exceed_stop():
    with pytest.raises(ValueError):
        seq = Linear(start=0.0, stop=1.0, duration=1.0)[:4.0]
        location.Square(1).rydberg.detuning.uniform.apply(seq).mock(10)


def test_integration_slice_linear_error_revese():
    with pytest.raises(ValueError):
        seq = Linear(start=0.0, stop=1.0, duration=1.0)[0.5:0.0]
        location.Square(1).rydberg.detuning.uniform.apply(seq).mock(10)


def test_integration_slice_linear_error_same_vals_nofield():
    with pytest.raises(ValueError):
        seq = Linear(start=0.0, stop=1.0, duration=1.0)[0.0:0.0]
        location.Square(1).rydberg.detuning.uniform.apply(seq).mock(10)


def test_integration_phase():
    job = (
        location.Square(1)
        .rydberg.rabi.phase.uniform.piecewise_constant(
            durations=[0.5, 0.5], values=[0, 1]
        )
        .mock(10)
    )

    panel = json.loads(job.json())

    print(panel)

    ir = panel["tasks"]["0"]["task_ir"]

    assert ir["nshots"] == 10
    assert ir["lattice"]["sites"][0] == [0.0, 0.0]
    assert ir["lattice"]["filling"] == [1]
    assert ir["lattice"]["filling"] == [1]

    phase_ir = ir["effective_hamiltonian"]["rydberg"]["rabi_frequency_phase"]
    assert all(phase_ir["global"]["times"] == np.array([0, 0.5, 1.0]) * 1e-6)
    assert all(phase_ir["global"]["values"] == np.array([0, 1.0, 1.0]))


def test_intergration_phase_nonconst_err():
    with pytest.raises(ValueError):
        (
            location.Square(1)
            .rydberg.rabi.phase.uniform.piecewise_linear(
                durations=[0.5, 0.5], values=[0, 1, 2]
            )
            .mock(10)
        )

    seq = Poly(checkpoints=[1, 2], duration=0.5)
    with pytest.raises(ValueError):
        location.Square(1).rydberg.rabi.phase.uniform.apply(seq).mock(10)


def test_integration_phase_linear():
    job = (
        location.Square(1)
        .rydberg.rabi.phase.uniform.linear(start=1, stop=1, duration=1)
        .mock(10)
    )

    panel = json.loads(job.json())

    print(panel)

    ir = panel["tasks"]["0"]["task_ir"]

    assert ir["nshots"] == 10
    assert ir["lattice"]["sites"][0] == [0.0, 0.0]
    assert ir["lattice"]["filling"] == [1]
    assert ir["lattice"]["filling"] == [1]

    phase_ir = ir["effective_hamiltonian"]["rydberg"]["rabi_frequency_phase"]
    assert all(phase_ir["global"]["times"] == np.array([0, 1.0]) * 1e-6)
    assert all(phase_ir["global"]["values"] == np.array([1.0, 1.0]))


def test_integration_phase_polyconst():
    seq = Poly(checkpoints=[1], duration=0.5)
    job = location.Square(1).rydberg.rabi.phase.uniform.apply(seq).mock(10)

    panel = json.loads(job.json())

    print(panel)

    ir = panel["tasks"]["0"]["task_ir"]

    assert ir["nshots"] == 10
    assert ir["lattice"]["sites"][0] == [0.0, 0.0]
    assert ir["lattice"]["filling"] == [1]
    assert ir["lattice"]["filling"] == [1]

    phase_ir = ir["effective_hamiltonian"]["rydberg"]["rabi_frequency_phase"]
    assert all(phase_ir["global"]["times"] == np.array([0, 0.5]) * 1e-6)
    assert all(phase_ir["global"]["values"] == np.array([1.0, 1.0]))


def test_integration_phase_slice():
    ##[Further investigate!]
    seq = Poly(checkpoints=[1], duration=1.0)[0:0.5]
    job = location.Square(1).rydberg.rabi.phase.uniform.apply(seq).mock(10)

    panel = json.loads(job.json())

    print(panel)

    ir = panel["tasks"]["0"]["task_ir"]

    assert ir["nshots"] == 10
    assert ir["lattice"]["sites"][0] == [0.0, 0.0]
    assert ir["lattice"]["filling"] == [1]
    assert ir["lattice"]["filling"] == [1]

    phase_ir = ir["effective_hamiltonian"]["rydberg"]["rabi_frequency_phase"]
    assert all(phase_ir["global"]["times"] == np.array([0, 0, 0.5]) * 1e-6)
    assert all(phase_ir["global"]["values"] == np.array([1.0, 1.0, 1.0]))


def test_integration_phase_scale():
    seq = 3.0 * Constant(value=1.0, duration=1.0)
    job = location.Square(1).rydberg.rabi.phase.uniform.apply(seq).mock(10)

    panel = json.loads(job.json())

    print(panel)

    ir = panel["tasks"]["0"]["task_ir"]

    assert ir["nshots"] == 10
    assert ir["lattice"]["sites"][0] == [0.0, 0.0]
    assert ir["lattice"]["filling"] == [1]
    assert ir["lattice"]["filling"] == [1]

    phase_ir = ir["effective_hamiltonian"]["rydberg"]["rabi_frequency_phase"]
    assert all(phase_ir["global"]["times"] == np.array([0, 1.0]) * 1e-6)
    assert all(phase_ir["global"]["values"] == np.array([3.0, 3.0]))


def test_integration_phase_neg():
    seq = -Constant(value=1.0, duration=1.0)
    job = location.Square(1).rydberg.rabi.phase.uniform.apply(seq).mock(10)

    panel = json.loads(job.json())

    print(panel)

    ir = panel["tasks"]["0"]["task_ir"]

    assert ir["nshots"] == 10
    assert ir["lattice"]["sites"][0] == [0.0, 0.0]
    assert ir["lattice"]["filling"] == [1]
    assert ir["lattice"]["filling"] == [1]

    phase_ir = ir["effective_hamiltonian"]["rydberg"]["rabi_frequency_phase"]
    assert all(phase_ir["global"]["times"] == np.array([0, 1.0]) * 1e-6)
    assert all(phase_ir["global"]["values"] == np.array([-1.0, -1.0]))


def test_integration_phase_slice_no_start():
    ##[Further investigate!]
    seq = Poly(checkpoints=[1], duration=1.0)[:0.5]
    job = location.Square(1).rydberg.rabi.phase.uniform.apply(seq).mock(10)

    panel = json.loads(job.json())

    print(panel)

    ir = panel["tasks"]["0"]["task_ir"]

    assert ir["nshots"] == 10
    assert ir["lattice"]["sites"][0] == [0.0, 0.0]
    assert ir["lattice"]["filling"] == [1]
    assert ir["lattice"]["filling"] == [1]

    phase_ir = ir["effective_hamiltonian"]["rydberg"]["rabi_frequency_phase"]
    assert all(phase_ir["global"]["times"] == np.array([0, 0, 0.5]) * 1e-6)
    assert all(phase_ir["global"]["values"] == np.array([1.0, 1.0, 1.0]))


def test_integration_phase_slice_no_stop():
    ##[Further investigate!]
    seq = Poly(checkpoints=[1], duration=0.5)[0:]
    job = location.Square(1).rydberg.rabi.phase.uniform.apply(seq).mock(10)

    panel = json.loads(job.json())

    print(panel)

    ir = panel["tasks"]["0"]["task_ir"]

    assert ir["nshots"] == 10
    assert ir["lattice"]["sites"][0] == [0.0, 0.0]
    assert ir["lattice"]["filling"] == [1]
    assert ir["lattice"]["filling"] == [1]

    phase_ir = ir["effective_hamiltonian"]["rydberg"]["rabi_frequency_phase"]
    assert all(phase_ir["global"]["times"] == np.array([0, 0, 0.5]) * 1e-6)
    assert all(phase_ir["global"]["values"] == np.array([1.0, 1.0, 1.0]))


def test_integration_phase_slice_error_neg_start():
    with pytest.raises(ValueError):
        ##[Further investigate!]
        seq = Poly(checkpoints=[1], duration=1.0)[-0.1:0.5]
        location.Square(1).rydberg.rabi.phase.uniform.apply(seq).mock(10)


def test_integration_phase_slice_error_exceed_stop():
    with pytest.raises(ValueError):
        ##[Further investigate!]
        seq = Poly(checkpoints=[1], duration=1.0)[0:2.0]
        location.Square(1).rydberg.rabi.phase.uniform.apply(seq).mock(10)


def test_integration_phase_slice_error_reverse():
    with pytest.raises(ValueError):
        ##[Further investigate!]
        seq = Poly(checkpoints=[1], duration=1.0)[2.0:0.0]
        location.Square(1).rydberg.rabi.phase.uniform.apply(seq).mock(10)
