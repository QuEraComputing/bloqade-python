import plum
from bloqade.emulate.ir.emulator import EmulatorProgram
from bloqade.emulate.ir.space import Space
from bloqade.emulate.sparse_operator import (
    IndexMapping,
    SparseMatrixCSC,
    SparseMatrixCSR,
)
from dataclasses import dataclass, field
from numpy.typing import NDArray
from beartype.typing import List, Callable, Union, Optional, Tuple
from beartype.vale import IsAttr, IsEqual
from typing import Annotated
from beartype import beartype
import numpy as np
from scipy.integrate import ode
from numba import njit

SparseOperator = Union[IndexMapping, SparseMatrixCSR, SparseMatrixCSC]


RealArray = Annotated[NDArray[np.floating], IsAttr["ndim", IsEqual[1]]]
Complexarray = Annotated[NDArray[np.complexfloating], IsAttr["ndim", IsEqual[1]]]
StateArray = Union[RealArray, Complexarray]


@njit(cache=True)
def _expt_one_body_op(configs, n_level, psi, site, op):
    res = np.zeros(psi.shape[1:], dtype=np.complex128)

    divisor = n_level**site

    for i, config in enumerate(configs):
        col = (config // divisor) % n_level
        for row, ele in enumerate(op[:, col]):
            j = config - (col * divisor) + (row * divisor)

            res += ele * psi[i, ...] * np.conj(psi[j, ...])

    return res


@njit(cache=True)
def _expt_two_body_op(configs, n_level, psi, sites, data, indices, indptr):
    res = np.zeros(psi.shape[1:], dtype=np.complex128)

    divisor_1 = n_level ** sites[0]
    divisor_2 = n_level ** sites[1]

    for i, config in enumerate(configs):
        col_1 = (config // divisor_1) % n_level
        col_2 = (config // divisor_2) % n_level
        col = col_1 + (col_2 * n_level)

        start = indptr[col]
        end = indptr[col + 1]

        for ele, row in zip(data[start:end], indices[start:end]):
            row_2, row_1 = divmod(row, n_level)

            j = (
                config
                - (col_1 * divisor_1)
                - (col_2 * divisor_2)
                + (row_1 * divisor_1)
                + (row_2 * divisor_2)
            )

            res += ele * psi[i, ...] * np.conj(psi[j, ...])

    return res


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

    def dot(self, register: NDArray, output: NDArray, time: float):
        amplitude = self.amplitude(time) / 2
        if self.phase is None:
            return self.op.matvec(register, out=output, scale=amplitude)

        amplitude *= np.exp(1j * self.phase(time))
        self.op.matvec(register, out=output, scale=amplitude)
        self.op.T.matvec(register, out=output, scale=np.conj(amplitude))

        return output


@dataclass(frozen=True)
class RydbergHamiltonian:
    emulator_ir: EmulatorProgram
    space: Space
    rydberg: NDArray
    detuning_ops: List[DetuningOperator] = field(default_factory=list)
    rabi_ops: List[RabiOperator] = field(default_factory=list)

    def _ode_complex_kernel(self, time: float, register: NDArray, output: NDArray):
        diagonal = sum(
            (detuning.get_diagonal(time) for detuning in self.detuning_ops),
            start=self.rydberg,
        )

        np.multiply(diagonal, register, out=output)
        for rabi_op in self.rabi_ops:
            rabi_op.dot(register, output, time)

        output *= -1j
        return output

    def _ode_real_kernel(self, time: float, register: NDArray, output: NDArray):
        # this is needed to use solver that only work on real-valued states
        return self._ode_complex_kernel(
            time, register.view(np.complex128), output
        ).view(np.float64)

    def _ode_complex_kernel_int(self, time: float, register: NDArray, output: NDArray):
        diagonal = sum(
            (detuning.get_diagonal(time) for detuning in self.detuning_ops),
        )

        u = np.exp(-1j * self.rydberg * time)

        int_register = u * register

        np.multiply(diagonal, int_register, out=output)
        for rabi_op in self.rabi_ops:
            rabi_op.dot(int_register, output, time)

        np.conj(u, out=u)
        np.multiply(u, output, out=output)

        output *= -1j
        return output

    def _ode_real_kernel_int(self, time: float, register: NDArray, output: NDArray):
        # this is needed to use solver that only work on real-valued states
        return self._ode_complex_kernel_int(
            time, register.view(np.complex128), output
        ).view(np.float64)

    def _check_register(self, register: np.ndarray):
        register_shape = (self.space.size,)
        if register.shape != register_shape:
            raise ValueError(
                f"Expecting `register` to have  shape {register_shape}, "
                f"got shape {register.shape}"
            )

    def _apply(
        self,
        register: np.ndarray,
        time: Optional[float] = None,
        output: Optional[NDArray] = None,
    ) -> np.ndarray:
        self._check_register(register)

        if time is None:
            time = self.emulator_ir.duration

        if output is None:
            output = np.zeros_like(register, dtype=np.complex128)

        diagonal = sum(
            (detuning.get_diagonal(time) for detuning in self.detuning_ops),
        )

        np.multiply(diagonal, register, out=output)

        for rabi_op in self.rabi_ops:
            rabi_op.dot(register, output, time)

        return output

    @beartype
    def average(
        self,
        register: np.ndarray,
        time: Optional[float] = None,
    ) -> float:
        """Get energy average from RydbergHamiltonian object at time `time` with
        register `register`

        Args:
            register (np.ndarray): Register as 1D array
            time (Optional[float], optional): Time value to evaluate average at.
            Defaults to duration of RydbergHamiltonian.

        Returns:
            float: average energy at time `time`
        """
        return np.vdot(register, self._apply(register, time)).real

    @beartype
    def average_and_variance(
        self,
        register: np.ndarray,
        time: Optional[float] = None,
    ) -> Tuple[float, float]:
        """Get energy average and variance from RydbergHamiltonian object at time `time`
        with register `register`

        Args:
            register (np.ndarray): Register as 1D array
            time (Optional[float], optional): Time value to evaluate average at.
            Defaults to duration of RydbergHamiltonian.

        Returns:
            Tuple[float, float]: average and variance of energy at time `time`
            respectively.
        """
        H_register = self._apply(register, time)

        average = np.vdot(register, H_register).real
        square_average = np.vdot(H_register, H_register).real

        return average, square_average - average**2

    def variance(
        self,
        register: np.ndarray,
        time: Optional[float] = None,
    ) -> float:
        """Get the energy variance from RydbergHamiltonian object at
        time `time` with register `register`

        Args:
            register (np.ndarray): Register as 1D array
            time (Optional[float], optional): Time value to evaluate average at.
            Defaults to duration of RydbergHamiltonian.

        Returns:
            complex: variance of energy at time `time` respectively.
        """

        _, var = self.average_and_variance(register, time)
        return var

    @plum.dispatch
    def expectation_value(
        self,
        register: np.ndarray,
        operator: np.ndarray,
        site_indices: Tuple[int, int],
    ) -> complex:
        from scipy.sparse import csc_array

        shape = (self.space.atom_type.n_level**2, self.space.atom_type.n_level**2)
        if operator.shape != shape:
            raise ValueError(
                f"expecting operator to be size {shape}, got site {operator.shape}"
            )

        csc_operator = csc_array(operator)

        value = _expt_two_body_op(
            configs=self.space.configurations,
            n_level=self.space.atom_type.n_level,
            psi=register,
            sites=site_indices,
            data=csc_operator.data,
            indices=csc_operator.indices,
            indptr=csc_operator.indptr,
        )

        return complex(value.real, value.imag)

    @plum.dispatch
    def expectation_value(  # noqa: F811
        self, register: np.ndarray, operator: np.ndarray, site_indices: int
    ) -> complex:
        """Calculate expectation values of one and two body operators.

        Args:
            register (np.ndarray): Register to evaluate expectation value with
            operator (np.ndarray): Operator to take expectation value of.
            site_indices (int, Tuple[int, int]): site/sites to evaluate `operator` at.
                It can either a single integer or a tuple of two integers for one and
                two body operator respectively.

        Raises:
            ValueError: Error is raised when the dimension of `operator` is not
            consistent with `site` argument. The size of the operator must fit the
            size of the local hilbert space of `site` depending on the number of sites
            and the number of levels inside each atom, e.g. for two site expectation v
            alue with a three level atom the operator must be a 9 by 9 array.

        Returns:
            complex: The expectation value.
        """
        self._check_register(register)

        shape = (self.space.atom_type.n_level, self.space.atom_type.n_level)
        if operator.shape != shape:
            raise ValueError(
                f"expecting operator to be size {shape}, got {operator.shape}"
            )

        value = _expt_one_body_op(
            configs=self.space.configurations,
            n_level=self.space.atom_type.n_level,
            psi=register,
            site=site_indices,
            op=operator,
        )

        return complex(value.real, value.imag)


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

    def _apply(
        self,
        state: StateArray,
        solver_name: str = "dop853",
        atol: float = 1e-7,
        rtol: float = 1e-14,
        nsteps: int = 2_147_483_647,
        times: Union[List[float], RealArray] = [],
    ):
        if state is None:
            state = self.hamiltonian.space.zero_state()

        if solver_name not in AnalogGate.SUPPORTED_SOLVERS:
            raise ValueError(f"'{solver_name}' not supported.")

        duration = self.hamiltonian.emulator_ir.duration

        state = np.asarray(state).astype(np.complex128, copy=False)

        solver = ode(self.hamiltonian._ode_real_kernel)
        solver.set_f_params(np.zeros_like(state, dtype=np.complex128))
        solver.set_initial_value(state.view(np.float64))
        solver.set_integrator(solver_name, atol=atol, rtol=rtol, nsteps=nsteps)

        if any(time >= duration or time < 0.0 for time in times):
            raise ValueError("Times must be between 0 and duration.")

        times = [*times, duration]

        for time in times:
            if time == 0.0:
                yield state
                continue
            solver.integrate(time)
            AnalogGate._error_check(solver_name, solver.get_return_code())
            yield solver.y.view(np.complex128)

    def _apply_interation_picture(
        self,
        state: StateArray,
        solver_name: str = "dop853",
        atol: float = 1e-7,
        rtol: float = 1e-14,
        nsteps: int = 2_147_483_647,
        times: Union[List[float], RealArray] = [],
    ):
        if state is None:
            state = self.hamiltonian.space.zero_state()

        if solver_name not in AnalogGate.SUPPORTED_SOLVERS:
            raise ValueError(f"'{solver_name}' not supported.")

        duration = self.hamiltonian.emulator_ir.duration

        state = np.asarray(state).astype(np.complex128, copy=False)

        solver = ode(self.hamiltonian._ode_real_kernel_int)
        solver.set_f_params(np.zeros_like(state, dtype=np.complex128))
        solver.set_initial_value(state.view(np.float64))
        solver.set_integrator(solver_name, atol=atol, rtol=rtol, nsteps=nsteps)

        if any(time >= duration or time < 0.0 for time in times):
            raise ValueError("Times must be between 0 and duration.")

        times = [*times, duration]

        for time in times:
            if time == 0.0:
                yield state
                continue
            solver.integrate(time)
            AnalogGate._error_check(solver_name, solver.get_return_code())
            u = np.exp(-1j * time * self.hamiltonian.rydberg)
            yield u * solver.y.view(np.complex128)

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
        if interaction_picture:
            return self._apply_interation_picture(
                state,
                solver_name=solver_name,
                atol=atol,
                rtol=rtol,
                nsteps=nsteps,
                times=times,
            )
        else:
            return self._apply(
                state,
                solver_name=solver_name,
                atol=atol,
                rtol=rtol,
                nsteps=nsteps,
                times=times,
            )

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
