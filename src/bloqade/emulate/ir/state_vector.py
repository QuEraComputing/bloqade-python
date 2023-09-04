from bloqade.emulate.ir.emulator import EmulatorProgram
from bloqade.emulate.ir.space import Space
from bloqade.emulate.sparse_operator import IndexMapping
from scipy.sparse import csr_matrix
from dataclasses import dataclass, field
from numpy.typing import NDArray
from typing import List, Callable, Union, Optional
import numpy as np
from scipy.integrate import ode

SparseOperator = Union[IndexMapping, csr_matrix]


@dataclass(frozen=True)
class DetuningOperator:
    diagonal: NDArray
    amplitude: Optional[Callable[[float], float]] = None

    def get_diagonal(self, time: float):
        if self.amplitude:
            return self.diagonal * self.amplitude(time)
        else:
            return self.diagonal


@dataclass(frozen=True)
class RabiOperator:
    op: SparseOperator
    amplitude: Callable[[float], float]
    phase: Optional[Callable[[float], float]] = None

    def dot(self, register: NDArray, time: float):
        amplitude = self.amplitude(time)
        if self.phase is None:
            return self.op.dot(register) * amplitude

        amplitude *= np.exp(1j * self.phase(time))
        output = self.op.dot(register) * amplitude
        output += self.op.T.dot(register) * np.conj(amplitude)

        return output


@dataclass(frozen=True)
class RydbergHamiltonian:
    emulator_ir: EmulatorProgram
    space: Space
    rydberg: NDArray
    detuning_ops: List[DetuningOperator] = field(default_factory=list)
    rabi_ops: List[RabiOperator] = field(default_factory=list)

    def _ode_complex_kernel(self, time: float, register: NDArray):
        diagonal = sum(
            (detuning.get_diagonal(time) for detuning in self.detuning_ops),
            start=self.rydberg,
        )

        result_register = diagonal * register
        for rabi_op in self.rabi_ops:
            result_register += rabi_op.dot(register, time)

        result_register *= -1j
        return result_register

    def _ode_real_kernel(self, time: float, register: NDArray):
        # this is needed to use solver that only work on real-valued states
        return self._ode_complex_kernel(time, register.view(np.complex128)).view(
            np.float64
        )


@dataclass(frozen=True)
class AnalogGate:
    SUPPORTED_SOLVERS = ["lsoda", "dop853", "dopri5"]

    hamiltonian: RydbergHamiltonian

    @staticmethod
    def _error_check_dop(status_code: int):
        match status_code:
            case 1 | 2:  # happy path
                pass
            case -1:
                raise RuntimeError("DOP853: Input is not consistent.")
            case -2:
                raise RuntimeError("DOP853: Larger nsteps is needed.")
            case -3:
                raise RuntimeError("DOP853: Step size becomes too small.")
            case -4:
                raise RuntimeError("DOP853: Problem is probably stiff (interrupted).")
            case _:
                raise RuntimeError(f"DOP853: unhandled status code {status_code}")

    @staticmethod
    def _error_check_lsoda(status_code: int):
        match status_code:
            case 2:  # happy path
                pass
            case -1:
                raise RuntimeError(
                    "LSODA: Excess work done on this call (perhaps wrong Dfun type)."
                )
            case -2:
                raise RuntimeError(
                    "LSODA: Excess accuracy requested (tolerances too small)."
                )
            case -3:
                raise RuntimeError("LSODA: Illegal input detected (internal error).")
            case -4:
                raise RuntimeError(
                    "LSODA: Repeated error test failures (internal error)."
                )
            case -5:
                raise RuntimeError(
                    "LSODA: Repeated convergence failures "
                    "(perhaps bad Jacobian or tolerances)."
                )
            case -6:
                raise RuntimeError("LSODA: Error weight became zero during problem.")
            case -7:
                raise RuntimeError(
                    "LSODA: Internal workspace insufficient to finish (internal error)."
                )
            case _:
                raise RuntimeError(f"LSODA: unhandled status code {status_code}")

    @staticmethod
    def _error_check(solver_name: str, status_code: int):
        match solver_name:
            case str("dop853") | str("dopri5"):
                AnalogGate._error_check_dop(status_code)
            case str("lsoda"):
                AnalogGate._error_check_lsoda(status_code)

    def apply(
        self,
        state: NDArray,
        solver_name: str = "dop853",
        atol: float = 1e-7,
        rtol: float = 1e-14,
        nsteps: int = 2_147_483_647,
    ):
        if state is None:
            state = self.hamiltonian.space.zero_state()

        if solver_name not in AnalogGate.SUPPORTED_SOLVERS:
            raise ValueError(f"'{solver_name}' not supported.")

        state = np.asarray(state).astype(np.complex128, copy=False)
        solver = ode(self.hamiltonian._ode_real_kernel)
        solver.set_initial_value(state.view(np.float64))
        solver.set_integrator(solver_name, atol=atol, rtol=rtol, nstep=nsteps)
        solver.integrate(self.hamiltonian.emulator_ir.duration)
        AnalogGate._error_check(solver_name, solver.get_return_code())

        return solver.y.view(np.complex128)

    def run(
        self,
        shots: int = 1,
        solver_name: str = "dop853",
        atol: float = 1e-7,
        rtol: float = 1e-14,
        nsteps: int = 2_147_483_647,
        project_hyperfine: bool = True,
    ):
        """Run the emulation with all atoms in the ground state,
        sampling the final state vector."""
        state = self.hamiltonian.space.zero_state()
        result = self.apply(state, solver_name, atol, rtol, nsteps)

        return self.hamiltonian.space.sample_state_vector(
            result, shots, project_hyperfine=project_hyperfine
        )
