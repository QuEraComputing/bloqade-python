import pytest
from bloqade import start
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
    ["phi", "interaction"], product(np.linspace(0, 2 * np.pi, 11), [True, False])
)
def test_solution(phi: float, interaction: bool):
    rabi_freq = 2 * np.pi
    if phi == 0:

        program = (
            start.add_position((0, 0))
            .rydberg.rabi.amplitude.uniform.constant(rabi_freq, 4)
            .detuning.uniform.constant(1.0, 4.0)
            .bloqade.python()
        )
    else:
        program = (
            start.add_position((0, 0))
            .rydberg.rabi.amplitude.uniform.constant(rabi_freq, 4)
            .rabi.phase.uniform.constant(phi, 4)
            .detuning.uniform.constant(1.0, 4.0)
            .bloqade.python()
        )
    [emu] = program.hamiltonian()

    times = np.linspace(0, 4, 101)
    state_iter = emu.evolve(times=times, interaction_picture=interaction)

    h = emu.hamiltonian.tocsr(0).toarray()

    e, v = np.linalg.eigh(h)
    psi0 = np.zeros(2)
    psi0[0] = 1

    for state, time in zip(state_iter, times):
        assert str(state)
        expected_data = v @ (np.diag(np.exp(-1j * e * time)) @ (v.T @ psi0))
        data = state.data.copy()

        expected_average = np.vdot(expected_data, h.dot(expected_data))
        expected_variance = (
            np.vdot(expected_data, (h @ h).dot(expected_data)) - expected_average**2
        )

        average = emu.hamiltonian.average(state, time=time)
        variance = emu.hamiltonian.variance(state, time=time)
        average_2, variance_2 = emu.hamiltonian.average_and_variance(state, time=time)

        assert np.allclose(data, expected_data)
        assert np.allclose(average, expected_average)
        assert np.allclose(average_2, expected_average)
        assert np.allclose(variance, expected_variance)
        assert np.allclose(variance_2, expected_variance)
