from bloqade import start
from bloqade.codegen.emulator_ir import EmulatorProgramCodeGen
from bloqade.emulate.codegen.hamiltonian import RydbergHamiltonianCodeGen
from bloqade.emulate.ir.state_vector import AnalogGate
import numpy as np


def callback(register, *_):
    return register


def test_run_callback():
    program = (
        start.add_position((0, 0))
        .add_position((0, 6.1))
        .rydberg.detuning.uniform.constant(15, 1)
        .rabi.amplitude.uniform.constant(15, 1)
    )

    bloqade_ir = program.parse_circuit()
    emulatir_ir = EmulatorProgramCodeGen().emit(bloqade_ir)
    hamiltonian = RydbergHamiltonianCodeGen().emit(emulatir_ir)

    state = hamiltonian.space.zero_state(np.complex128)
    (expected_result,) = AnalogGate(hamiltonian).apply(state, atol=1e-14, rtol=1e-7)

    (result_single,) = program.bloqade.python().run_callback(callback)
    (result_multi,) = program.bloqade.python().run_callback(
        callback, multiprocessing=True, num_workers=1
    )

    np.testing.assert_equal(expected_result, result_single)
    np.testing.assert_equal(expected_result, result_multi)


if __name__ == "__main__":
    test_run_callback()
