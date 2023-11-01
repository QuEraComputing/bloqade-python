from bloqade import start
from bloqade.codegen.emulator_ir import EmulatorProgramCodeGen
from bloqade.emulate.codegen.hamiltonian import RydbergHamiltonianCodeGen
from bloqade.emulate.ir.state_vector import AnalogGate
import numpy as np
import pytest


def callback(register, *_):
    return register


def test_run_callback():
    program = (
        start.add_position((0, 0))
        .add_position((0, 6.1))
        .rydberg.detuning.uniform.constant(15, 0.1)
        .rabi.amplitude.uniform.constant(15, 0.1)
    )

    bloqade_ir = program.parse_circuit()
    emulatir_ir = EmulatorProgramCodeGen().emit(bloqade_ir)
    hamiltonian = RydbergHamiltonianCodeGen().emit(emulatir_ir)

    state = hamiltonian.space.zero_state(np.complex128)
    (expected_result,) = AnalogGate(hamiltonian).apply(state)

    (result_single,) = program.bloqade.python().run_callback(callback)
    (result_multi,) = program.bloqade.python().run_callback(
        callback, multiprocessing=True, num_workers=1
    )

    np.testing.assert_equal(expected_result, result_single)
    np.testing.assert_equal(expected_result, result_multi)


def callback_exception(*args):
    raise ValueError


def test_run_callback_exception():
    program = (
        start.add_position((0, 0))
        .add_position((0, 6.1))
        .rydberg.detuning.uniform.constant(15, 1)
        .rabi.amplitude.uniform.constant(15, 1)
    )

    # program.bloqade.python().run_callback(callback_exception)

    with pytest.raises(RuntimeError):
        program.bloqade.python().run_callback(callback_exception)

    with pytest.raises(RuntimeError):
        program.bloqade.python().run_callback(
            callback_exception, multiprocessing=True, num_workers=1
        )

    (result_single,) = program.bloqade.python().run_callback(
        callback_exception, ignore_exceptions=True
    )
    (result_multi,) = program.bloqade.python().run_callback(
        callback_exception, multiprocessing=True, num_workers=1, ignore_exceptions=True
    )

    assert isinstance(result_single, ValueError)
    assert isinstance(result_multi, ValueError)


if __name__ == "__main__":
    test_run_callback()
    test_run_callback_exception()
