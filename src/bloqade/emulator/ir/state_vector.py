from ast import Tuple
from bloqade.emulator.sparse_operator import IndexMapping, Diagonal

from pydantic import BaseModel
from scipy.sparse import csr_matrix
from numpy.typing import NDArray
from typing import List, Callable, Union
import numpy as np
from scipy.integrate import ode


class AnalogGate(BaseModel):
    SUPPORTED_SOLVERS = ["lsoda", "dop853", "dopri5"]

    terms: List[Tuple[Callable, Union[Diagonal, IndexMapping, csr_matrix]]]
    initial_time: float
    final_time: float
    atol: float = 1e-7
    rtol: float = 1e-14
    nsteps: int = 2_147_483_647

    def _ode_complex_kernel(self, time: float, register: NDArray):
        result_register = np.zeros_like(register)
        for function, operator in self.terms:
            if function is None:
                result_register += operator.dot(register)
            else:
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

    def _solve(self, state: NDArray, solver_name: str):
        state = np.asarray(state, dtype=np.complex128)
        solver = ode(self._ode_real_kernel)
        solver.set_initial_value(state.view(np.float64), self.initial_time)
        solver.set_integrator(
            solver_name, atol=self.atol, rtol=self.rtol, nstep=self.nsteps
        )
        solver.integrate(self.final_time)
        AnalogGate._error_check(solver_name, solver.get_return_code())

        return solver.y.view(np.complex128)

    def apply(self, state: NDArray, solver_name="lsoda"):
        if solver_name not in AnalogGate.SUPPORTED_SOLVERS:
            raise ValueError(f"'{solver_name}' not supported.")

        return self._solve(state, "lsoda")
