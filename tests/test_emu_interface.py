import pytest
from bloqade import start
from bloqade.atom_arrangement import Chain
import numpy as np
from itertools import product


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
        .rydberg.detuning.uniform.constant(1.0, 4.0)
        .amplitude.uniform.constant(rabi_freq, 4)
    )

    if phi != 0:
        program = program.phase.uniform.constant(phi, 4)

    [emu] = program.bloqade.python().hamiltonian()

    times = np.linspace(0, 4, 101)
    state_iter = emu.evolve(times=times, interaction_picture=interaction)

    h = emu.hamiltonian.tocsr(0)

    e, v = np.linalg.eigh(h.toarray())

    psi0 = emu.zero_state().data

    for state, time in zip(state_iter, times):
        assert str(state)
        expected_data = v @ (np.diag(np.exp(-1j * e * time)) @ (v.T @ psi0))
        data = state.data

        expected_average = np.vdot(expected_data, h.dot(expected_data))
        expected_variance = (
            np.vdot(expected_data, (h @ h).dot(expected_data)) - expected_average**2
        )

        average = emu.hamiltonian.average(state, time=time)
        variance = emu.hamiltonian.variance(state, time=time)
        average_2, variance_2 = emu.hamiltonian.average_and_variance(state, time=time)

        assert np.allclose(data, expected_data), "failed at time {}".format(time)
        assert np.allclose(average, expected_average), "failed at time {}".format(time)
        assert np.allclose(average_2, expected_average), "failed at time {}".format(
            time
        )
        assert np.allclose(variance, expected_variance), "failed at time {}".format(
            time
        )
        assert np.allclose(variance_2, expected_variance), "failed at time {}".format(
            time
        )
