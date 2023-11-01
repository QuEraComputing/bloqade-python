from bloqade import start
import numpy as np


def callback_single_atom(register, *_):
    density_op = np.array([[0.0, 0.0], [0, 1]])
    rabi_op = np.array([[0.0, -1.0j], [+1.0j, 0.0]])

    density = register.local_trace(density_op, 0)
    rabi_expt = register.local_trace(rabi_op, 0)

    exact_density = np.vdot(register.data, density_op.dot(register.data))
    exact_rabi_expt = np.vdot(register.data, rabi_op.dot(register.data))

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
        .run_callback(callback=callback_single_atom)
    )


def callback_two_atom(register, *_):
    density_op = np.array([[0.0, 0.0], [0.0, 1.0]])
    rabi_op = np.array([[0.0, -1.0j], [0.0j, 0.0]])

    full_density_op_0 = np.kron(np.eye(2), density_op)
    full_density_op_1 = np.kron(density_op, np.eye(2))
    full_rabi_op_0 = np.kron(np.eye(2), rabi_op)
    full_rabi_op_1 = np.kron(rabi_op, np.eye(2))

    density_0 = register.local_trace(density_op, 0)
    density_1 = register.local_trace(density_op, 1)
    rabi_expt_0 = register.local_trace(rabi_op, 0)
    rabi_expt_1 = register.local_trace(rabi_op, 1)

    exact_density_0 = np.vdot(register.data, full_density_op_0.dot(register.data))
    exact_density_1 = np.vdot(register.data, full_density_op_1.dot(register.data))
    exact_rabi_expt_0 = np.vdot(register.data, full_rabi_op_0.dot(register.data))
    exact_rabi_expt_1 = np.vdot(register.data, full_rabi_op_1.dot(register.data))

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
        .run_callback(callback=callback_two_atom)
    )


def callback_two_body(register, *_):
    from functools import reduce

    plus_op = np.array([[0.0, 1.0], [0.0, 0.0]])
    minus_op = np.array([[0.0, 0.0], [1.0, 0.0]])

    two_body_operator = np.kron(minus_op, plus_op)
    # reverse order
    full_body_operator = reduce(np.kron, [plus_op, np.eye(2), minus_op])

    corr = register.local_trace(two_body_operator, (0, 2))

    expected_corr = np.vdot(register.data, full_body_operator.dot(register.data))

    np.testing.assert_almost_equal(corr, expected_corr)


def test_expectation_value_two_body():
    omega = 2 * np.pi
    (
        start.add_position((0, 0))
        .add_position((0, 6.1))
        .add_position((6.1, 6.1))
        .rydberg.rabi.amplitude.uniform.constant("omega", "run_time")
        .assign(omega=omega)
        .batch_assign(run_time=np.linspace(0, 2 * np.pi / omega, 11))
        .bloqade.python()
        .run_callback(callback=callback_two_body)
    )


if __name__ == "__main__":
    test_expectation_value_single_atom()
    test_expection_value_two_atom()
    test_expectation_value_two_body()
