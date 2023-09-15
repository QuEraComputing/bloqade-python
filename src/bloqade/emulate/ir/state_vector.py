from bloqade.emulate.ir.emulator import EmulatorProgram
from bloqade.emulate.ir.space import Space
from bloqade.emulate.sparse_operator import IndexMapping
from scipy.sparse import csr_matrix
from dataclasses import dataclass, field
from numpy.typing import NDArray
from beartype.typing import List, Callable, Union, Optional
from beartype.vale import IsAttr, IsEqual
from typing import Annotated
from beartype import beartype
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

    def _ode_complex_kernel_int(self, time: float, register: NDArray):
        diagonal = sum(
            (detuning.get_diagonal(time) for detuning in self.detuning_ops),
        )

        u = np.exp(-1j * self.rydberg * time)

        int_register = u * register

        result_register = diagonal * int_register
        for rabi_op in self.rabi_ops:
            result_register += rabi_op.dot(int_register, time)

        np.conj(u, out=u)
        np.multiply(u, result_register, out=result_register)

        result_register *= -1j
        return result_register

    def _ode_real_kernel_int(self, time: float, register: NDArray):
        # this is needed to use solver that only work on real-valued states
        return self._ode_complex_kernel_int(time, register.view(np.complex128)).view(
            np.float64
        )


RealArray = Annotated[NDArray[np.floating], IsAttr["ndim", IsEqual[1]]]
Complexarray = Annotated[NDArray[np.complexfloating], IsAttr["ndim", IsEqual[1]]]
StateArray = Union[RealArray, Complexarray]


@dataclass(frozen=True)
class AnalogGate:
    SUPPORTED_SOLVERS = ["lsoda", "dop853", "dopri5"]

    hamiltonian: RydbergHamiltonian

    @staticmethod
    def _error_check_dop(status_code: int):
        if status_code in [1, 2]:
            return
        elif status_code == -1:
            raise RuntimeError("DOP853/DOPRI5: Input is not consistent.")
        elif status_code == -2:
            raise RuntimeError("DOP853/DOPRI5: Larger nsteps is needed.")
        elif status_code == -3:
            raise RuntimeError("DOP853/DOPRI5: Step size becomes too small.")
        elif status_code == -4:
            raise RuntimeError(
                "DOP853/DOPRI5: Problem is probably stiff (interrupted)."
            )
        else:
            raise RuntimeError(f"DOP853/DOPRI5: unhandled status code {status_code}")

    @staticmethod
    def _error_check_lsoda(status_code: int):
        if status_code == 2:
            return
        elif status_code == -1:
            raise RuntimeError(
                "LSODA: Excess work done on this call (perhaps wrong Dfun type)."
            )
        elif status_code == -2:
            raise RuntimeError(
                "LSODA: Excess accuracy requested (tolerances too small)."
            )
        elif status_code == -3:
            raise RuntimeError("LSODA: Illegal input detected (internal error).")
        elif status_code == -4:
            raise RuntimeError("LSODA: Repeated error test failures (internal error).")
        elif status_code == -5:
            raise RuntimeError(
                "LSODA: Repeated convergence failures "
                "(perhaps bad Jacobian or tolerances)."
            )
        elif status_code == -6:
            raise RuntimeError("LSODA: Error weight became zero during problem.")
        elif status_code == -7:
            raise RuntimeError(
                "LSODA: Internal workspace insufficient to finish (internal error)."
            )
        else:
            raise RuntimeError(f"LSODA: unhandled status code {status_code}")

    @staticmethod
    def _error_check(solver_name: str, status_code: int):
        if solver_name == "lsoda":
            AnalogGate._error_check_lsoda(status_code)
        elif solver_name in ["dop853", "dopri5"]:
            AnalogGate._error_check_dop(status_code)

    @beartype
    def apply(
        self,
        state: StateArray,
        solver_name: str = "dop853",
        atol: float = 1e-7,
        rtol: float = 1e-14,
        nsteps: int = 2_147_483_647,
        times: Union[List[float], RealArray] = [],
        interaction_picture: bool = False,
    ):
        if state is None:
            state = self.hamiltonian.space.zero_state()

        if solver_name not in AnalogGate.SUPPORTED_SOLVERS:
            raise ValueError(f"'{solver_name}' not supported.")

        duration = self.hamiltonian.emulator_ir.duration

        state = np.asarray(state).astype(np.complex128, copy=False)

        if interaction_picture:
            solver = ode(self.hamiltonian._ode_real_kernel_int)
        else:
            solver = ode(self.hamiltonian._ode_real_kernel)

        solver.set_initial_value(state.view(np.float64))
        solver.set_integrator(solver_name, atol=atol, rtol=rtol, nsteps=nsteps)

        if any(time >= duration or time < 0.0 for time in times):
            raise ValueError("Times must be between 0 and duration.")

        times = [*times, duration]

        for time in times:
            solver.integrate(time)
            AnalogGate._error_check(solver_name, solver.get_return_code())
            u = np.exp(-1j * time * self.hamiltonian.rydberg)
            yield u * solver.y.view(np.complex128)

    @beartype
    def run(
        self,
        shots: int = 1,
        solver_name: str = "dop853",
        atol: float = 1e-14,
        rtol: float = 1e-7,
        nsteps: int = 2_147_483_647,
        interaction_picture: bool = False,
        project_hyperfine: bool = True,
    ):
        """Run the emulation with all atoms in the ground state,
        sampling the final state vector."""

        options = dict(
            solver_name=solver_name,
            atol=atol,
            rtol=rtol,
            nsteps=nsteps,
            interaction_picture=interaction_picture,
        )
        state = self.hamiltonian.space.zero_state()
        (result,) = self.apply(state, **options)
        result /= np.linalg.norm(result)
        return self.hamiltonian.space.sample_state_vector(
            result, shots, project_hyperfine=project_hyperfine
        )
