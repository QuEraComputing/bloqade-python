import pytest
from bloqade import start
from bloqade.atom_arrangement import Chain
import numpy as np
from itertools import product
from math import isclose


def test_zero_state():
    [emu] = (
        start.add_position([(0, 0), (0, 5), (0, 10)])
        .rydberg.rabi.amplitude.uniform.constant(15.0, 4.0)
        .detuning.uniform.constant(1.0, 4.0)
        .bloqade.python()
        .hamiltonian()
    )

    data = np.zeros(8)
    data[0] = 1

    assert np.array_equal(emu.zero_state().data, data)


def test_fock_state():
    [emu] = (
        start.add_position([(0, 0), (0, 5), (0, 10)])
        .rydberg.rabi.amplitude.uniform.constant(15.0, 4.0)
        .detuning.uniform.constant(1.0, 4.0)
        .bloqade.python()
        .hamiltonian()
    )

    for idx, bitstring in enumerate(product("gr", repeat=3)):
        sv = emu.fock_state("".join(bitstring[::-1]))
        data = np.zeros(8)
        data[idx] = 1
        assert np.array_equal(sv.data, data)


@pytest.mark.parametrize(
    ["N", "phi", "interaction"],
    product([1, 2, 3, 4, 5], np.linspace(0, 2 * np.pi, 4), [True, False]),
)
def test_solution(N: int, phi: float, interaction: bool):
    rabi_freq = 2 * np.pi
    program = (
        Chain(N, lattice_spacing=6)
        # .rydberg.detuning.uniform.constant(1.0, 4.0)
        .rydberg.rabi.amplitude.uniform.constant(rabi_freq, 4.0)
    )

    if phi != 0:
        program = program.phase.uniform.constant(phi, 4)

    [emu] = program.bloqade.python().hamiltonian()

    times = np.linspace(0, 4, 101)
    state_iter = emu.evolve(
        times=times, interaction_picture=interaction, atol=1e-10, rtol=1e-14
    )

    h = emu.hamiltonian.tocsr(0)
    print(h.toarray())
    e, v = np.linalg.eigh(h.toarray())

    psi0 = emu.zero_state().data

    for state, time in zip(state_iter, times):
        assert str(state)
        expected_data = v @ (np.diag(np.exp(-1j * e * time)) @ (v.T.conj() @ psi0))
        data = state.data

        expected_average = np.vdot(expected_data, h.dot(expected_data)).real
        expected_variance = (
            np.vdot(expected_data, (h @ h).dot(expected_data)) - expected_average**2
        ).real

        print(emu.hamiltonian._apply(state.data, time) - h.dot(expected_data))

        average = emu.hamiltonian.average(state, time=time)
        variance = emu.hamiltonian.variance(state, time=time)
        average_2, variance_2 = emu.hamiltonian.average_and_variance(state, time=time)
        overlap = np.vdot(data, expected_data)
        assert isclose(overlap, 1.0, abs_tol=1e-7), f"failed data at time {time}"
        assert isclose(
            average, expected_average, rel_tol=1e-7, abs_tol=1e-7
        ), f"failed average at time {time}"
        assert isclose(
            average_2, expected_average, rel_tol=1e-7, abs_tol=1e-7
        ), f"failed average_2 at time {time}"
        assert isclose(
            variance, expected_variance, rel_tol=1e-7, abs_tol=1e-7
        ), f"failed variance at time {time}"
        assert isclose(
            variance_2, expected_variance, rel_tol=1e-7, abs_tol=1e-7
        ), f"failed variance_2 at time {time}"

    # assert False
