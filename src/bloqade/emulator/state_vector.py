from pydantic import BaseModel
from scipy.sparse import csr_matrix
from bloqade.emulator.sparse_operator import IndexMapping, Diagonal
from numpy.typing import NDArray
from typing import List, Callable, Union
import numpy as np
from scipy.integrate import ode


class AnalogGate(BaseModel):
    functions: List[Callable]
    operators: List[Union[Diagonal, IndexMapping, csr_matrix]]
    initial_time: float
    final_time: float
    atol: float = 1e-7
    rtol: float = 1e-14

    def _ode_complex_kernel(self, time: float, register: NDArray):
        result_register = np.zeros_like(register)
        for function, operator in zip(self.functions, self.operators):
            result_register += function(time + self.initial_time) * operator.dot(
                register
            )

        return result_register

    def _ode_real_kernel(self, time: float, register: NDArray):
        # this is needed to use solver that only work on real-valued states
        return self._ode_complex_kernel(time, register.view(np.complex128)).view(
            np.float64
        )

    @staticmethod
    def _error_dop853(status_code: int):
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

    @staticmethod
    def _error_lsoda(status_code: int):
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

    def _solve_lsoda(self, state: NDArray):
        state = np.asarray(state, dtype=np.complex128)
        solver = ode(self._ode_real_kernel)
        solver.set_initial_value(state.view(np.float64), self.initial_time)
        solver.set_integrator(
            "lsoda", atol=self.atol, rtol=self.rtol, nstep=np.iinfo(np.int32).max
        )
        solver.integrate(self.final_time)
        AnalogGate._error_lsoda(solver.get_return_code())

        return solver.y.view(np.complex128)

    def _solve_dop853(self, state: NDArray):
        state = np.asarray(state, dtype=np.complex128)
        solver = ode(self._ode_real_kernel)
        solver.set_initial_value(state.view(np.float64), self.initial_time)
        solver.set_integrator(
            "dop853", atol=self.atol, rtol=self.rtol, nstep=np.iinfo(np.int32).max
        )
        solver.integrate(self.final_time)
        AnalogGate._error_dop853(solver.get_return_code())

        return solver.y.view(np.complex128)

    def apply(self, state: NDArray, solver_name="lsoda"):
        match solver_name:
            case str("lsoda"):
                return self._solve_lsoda(state)
            case _:
                raise ValueError(f"Solver {solver_name} not supported")
