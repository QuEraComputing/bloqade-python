from bloqade import start
import numpy as np


def callback_single_atom(register, metadata, hamiltonian):
    density_op = np.array([[0, 0], [0, 1]])
    rabi_op = np.array([[0, -1j], [+1j, 0]])

    density = hamiltonian.expectation_value(register, density_op, 0)
    rabi_expt = hamiltonian.expectation_value(register, rabi_op, 0)

    exact_density = np.vdot(register, density_op.dot(register))
    exact_rabi_expt = np.vdot(register, rabi_op.dot(register))

    np.testing.assert_almost_equal(exact_density, density)
    np.testing.assert_almost_equal(exact_rabi_expt, rabi_expt)


def test_expectation_value_single_atom():
    omega = 2 * np.pi
    (
        start.add_position((0, 0))
        .rydberg.rabi.amplitude.uniform.constant("omega", "run_time")
        .assign(omega=omega)
        .batch_assign(run_time=np.linspace(0, 2 * np.pi / omega, 101))
        .bloqade.python()
        .run_callback(
            callback=callback_single_atom, multiprocessing=True, num_workers=2
        )
    )


def callback_two_atom(register, metadata, hamiltonian):
    density_op = np.array([[0, 0], [0, 1]])
    rabi_op = np.array([[0, -1j], [+1j, 0]])

    full_density_op_0 = np.kron(np.eye(2), density_op)
    full_density_op_1 = np.kron(density_op, np.eye(2))
    full_rabi_op_0 = np.kron(np.eye(2), rabi_op)
    full_rabi_op_1 = np.kron(rabi_op, np.eye(2))

    density_0 = hamiltonian.expectation_value(register, density_op, 0)
    density_1 = hamiltonian.expectation_value(register, density_op, 1)
    rabi_expt_0 = hamiltonian.expectation_value(register, rabi_op, 0)
    rabi_expt_1 = hamiltonian.expectation_value(register, rabi_op, 1)

    exact_density_0 = np.vdot(register, full_density_op_0.dot(register))
    exact_density_1 = np.vdot(register, full_density_op_1.dot(register))
    exact_rabi_expt_0 = np.vdot(register, full_rabi_op_0.dot(register))
    exact_rabi_expt_1 = np.vdot(register, full_rabi_op_1.dot(register))

    np.testing.assert_almost_equal(exact_density_0, density_0)
    np.testing.assert_almost_equal(exact_density_1, density_1)

    np.testing.assert_almost_equal(exact_rabi_expt_0, rabi_expt_0)
    np.testing.assert_almost_equal(exact_rabi_expt_1, rabi_expt_1)


def test_expection_value_two_atom():
    omega = 2 * np.pi
    (
        start.add_position((0, 0))
        .add_position((0, 6.1))
        .rydberg.rabi.amplitude.uniform.constant("omega", "run_time")
        .assign(omega=omega)
        .batch_assign(run_time=np.linspace(0, 2 * np.pi / omega, 11))
        .bloqade.python()
        .run_callback(callback=callback_two_atom, multiprocessing=True, num_workers=2)
    )


if __name__ == "__main__":
    test_expectation_value_single_atom()
    # test_expection_value_two_atom()
