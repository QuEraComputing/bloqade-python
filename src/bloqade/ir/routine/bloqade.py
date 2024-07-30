from collections import OrderedDict, namedtuple, abc

from bloqade.emulate.ir.emulator import EmulatorProgram
from bloqade.ir.routine.base import RoutineBase, __pydantic_dataclass_config__
from bloqade.builder.typing import LiteralType
from bloqade.task.batch import LocalBatch
from beartype import beartype
from beartype.typing import (
    Optional,
    Tuple,
    Callable,
    Dict,
    Any,
    List,
    NamedTuple,
    Iterator,
    Sequence,
)
from pydantic.v1.dataclasses import dataclass
import dataclasses
import numpy as np

from bloqade.emulate.codegen.hamiltonian import CompileCache, RydbergHamiltonianCodeGen
from bloqade.emulate.ir.state_vector import AnalogGate, RydbergHamiltonian, StateVector
import traceback


@dataclass(frozen=True, config=__pydantic_dataclass_config__)
class BloqadeServiceOptions(RoutineBase):
    def python(self):
        return BloqadePythonRoutine(self.source, self.circuit, self.params)


def cast_to_float(x):
    if isinstance(x, abc.Sequence):
        return [float(i) for i in x]
    else:
        return float(x)


@dataclasses.dataclass(frozen=True)
class TaskData:
    """Data class to hold the program ir and metadata for a given set of parameters"""

    task_id: int
    emulator_ir: EmulatorProgram
    metadata_dict: Dict[str, LiteralType]

    @property
    def metadata(self) -> NamedTuple:
        MetaData = namedtuple("MetaData", self.metadata_dict.keys())
        return MetaData(**{k: cast_to_float(v) for k, v in self.metadata_dict.items()})


@dataclasses.dataclass(frozen=True)
class BloqadeEmulation:
    """Data class to hold the Hamiltonian and metadata for a given set of parameters"""

    task_data: TaskData
    compile_cache: Optional[CompileCache] = None
    _hamiltonian: Optional[RydbergHamiltonian] = dataclasses.field(
        init=False, default=None
    )

    @property
    def hamiltonian(self) -> RydbergHamiltonian:
        """Return the Hamiltonian object for the given task data."""
        if self._hamiltonian is None:
            _hamiltonian = RydbergHamiltonianCodeGen(self.compile_cache).emit(
                self.task_data.emulator_ir
            )
            object.__setattr__(self, "_hamiltonian", _hamiltonian)
        return self._hamiltonian

    @property
    def metadata(self) -> NamedTuple:
        """The metadata for the given task data."""
        return self.task_data.metadata

    def zero_state(self, dtype: np.dtype = np.float64) -> StateVector:
        """Return the zero state for the given Hamiltonian."""
        return self.hamiltonian.space.zero_state(dtype)

    def fock_state(
        self, fock_state_str: str, dtype: np.dtype = np.float64
    ) -> StateVector:
        """Return the fock state for the given Hamiltonian."""
        index = self.hamiltonian.space.fock_state_to_index(fock_state_str)
        data = np.zeros(self.hamiltonian.space.size, dtype=dtype)
        data[index] = 1
        return StateVector(data, self.hamiltonian.space)

    def evolve(
        self,
        state: Optional[StateVector] = None,
        solver_name: str = "dop853",
        atol: float = 1e-7,
        rtol: float = 1e-14,
        nsteps: int = 2147483647,
        times: Sequence[float] = (),
        interaction_picture: bool = False,
    ) -> Iterator[StateVector]:
        """Evolve an initial state vector using the Hamiltonian

        Args:
            state (Optional[StateVector], optional): The initial state vector to
            evolve. if not provided, the zero state will be used. Defaults to None.
            solver_name (str, optional): Which SciPy Solver to use. Defaults to
            "dop853".
            atol (float, optional): Absolute tolerance for ODE solver. Defaults
            to 1e-14.
            rtol (float, optional): Relative tolerance for adaptive step in
            ODE solver. Defaults to 1e-7.
            nsteps (int, optional): Maximum number of steps allowed per integration
            step. Defaults to 2147483647.
            times (Sequence[float], optional): The times to evaluate the state vector
            at. Defaults to (). If not provided the state will be evaluated at
            the end of the bloqade program.
            interaction_picture (bool, optional): Use the interaction picture when
            solving schrodinger equation. Defaults to False.

        Returns:
            Iterator[StateVector]: An iterator of the state vectors at each time step.

        """
        state = self.zero_state(np.complex128) if state is None else state

        U = AnalogGate(self.hamiltonian)

        return U.apply(
            state,
            times=times,
            solver_name=solver_name,
            atol=atol,
            rtol=rtol,
            nsteps=nsteps,
            interaction_picture=interaction_picture,
        )


@dataclass(frozen=True, config=__pydantic_dataclass_config__)
class BloqadePythonRoutine(RoutineBase):
    @staticmethod
    def process_tasks(runner, tasks, results):
        while not tasks.empty():
            try:
                task_id, (emulator_ir, metadata) = tasks.get()
                result = runner.run_task(emulator_ir, metadata)
                results.put((task_id, result))
            except BaseException as e:
                results.put((task_id, e))

    @dataclass(config=__pydantic_dataclass_config__)
    class EmuRunner:
        compile_cache: Optional[CompileCache]
        solver_args: Dict
        callback: Callable
        callback_args: Tuple

        def run_task(self, emulator_ir, metadata_dict):
            hamiltonian = RydbergHamiltonianCodeGen(
                compile_cache=self.compile_cache
            ).emit(emulator_ir)

            MetaData = namedtuple("MetaData", metadata_dict.keys())
            metadata = MetaData(
                **{k: cast_to_float(v) for k, v in metadata_dict.items()}
            )
            zero_state = hamiltonian.space.zero_state(np.complex128)
            (wrapped_register,) = AnalogGate(hamiltonian).apply(
                zero_state, **self.solver_args
            )
            return self.callback(
                wrapped_register, metadata, hamiltonian, *self.callback_args
            )

    def _generate_ir(
        self, args, blockade_radius, waveform_runtime, use_hyperfine
    ) -> Iterator[TaskData]:
        from bloqade.compiler.passes.emulator import (
            flatten,
            assign,
            generate_emulator_ir,
        )

        params = self.params
        circuit = flatten(self.circuit)

        for task_number, batch_param in enumerate(params.batch_assignments(*args)):
            assignment = {**params.static_params, **batch_param}
            metadata, final_circuit = assign(assignment, circuit)
            emulator_ir = generate_emulator_ir(
                final_circuit, blockade_radius, waveform_runtime, use_hyperfine
            )
            yield TaskData(task_number, emulator_ir, metadata)

    def _compile(
        self,
        shots: int,
        args: Tuple[LiteralType, ...] = (),
        name: Optional[str] = None,
        blockade_radius: LiteralType = 0.0,
        cache_matrices: bool = False,
        waveform_runtime: str = "interpret",
        use_hyperfine: bool = False,
    ) -> LocalBatch:
        from bloqade.task.bloqade import BloqadeTask

        if cache_matrices:
            matrix_cache = CompileCache()
        else:
            matrix_cache = None

        tasks = OrderedDict()
        ir_iter = self._generate_ir(
            args, blockade_radius, waveform_runtime, use_hyperfine
        )
        for task_data in ir_iter:
            task_number = task_data.task_id
            emulator_ir = task_data.emulator_ir
            metadata = task_data.metadata_dict
            tasks[task_number] = BloqadeTask(shots, emulator_ir, metadata, matrix_cache)

        return LocalBatch(self.source, tasks, name)

    @beartype
    def run(
        self,
        shots: int,
        args: Tuple[LiteralType, ...] = (),
        name: Optional[str] = None,
        blockade_radius: float = 0.0,
        waveform_runtime: str = "interpret",
        interaction_picture: bool = False,
        cache_matrices: bool = False,
        multiprocessing: bool = False,
        num_workers: Optional[int] = None,
        solver_name: str = "dop853",
        atol: float = 1e-7,
        rtol: float = 1e-14,
        nsteps: int = 2_147_483_647,
    ) -> LocalBatch:
        """Run the current program using bloqade python backend

        Args:
            shots (int): number of shots after running state vector simulation
            args (Tuple[LiteralType, ...], optional): The values for parameters defined
            in `args`. Defaults to ().
            name (Optional[str], optional): Name to give this run. Defaults to None.
            blockade_radius (float, optional): Use the Blockade subspace given a
            particular radius. Defaults to 0.0.
            waveform_runtime: (bool, optional): Use Numba to compile the waveforms,
            Defaults to False.
            interaction_picture (bool, optional): Use the interaction picture when
            solving schrodinger equation. Defaults to False.
            cache_matrices (bool, optional): Reuse previously evaluated matrcies when
            possible. Defaults to False.
            multiprocessing (bool, optional): Use multiple processes to process the
            batches. Defaults to False.
            num_workers (Optional[int], optional): Number of processes to run with
            multiprocessing. Defaults to None.
            solver_name (str, optional): Which SciPy Solver to use. Defaults to
            "dop853".
            atol (float, optional): Absolute tolerance for ODE solver. Defaults to
            1e-14.
            rtol (float, optional): Relative tolerance for adaptive step in ODE solver.
            Defaults to 1e-7.
            nsteps (int, optional): Maximum number of steps allowed per integration
            step. Defaults to 2_147_483_647, the maximum value.

        Raises:
            ValueError: Cannot use multiprocessing and cache_matrices at the same time.

        Returns:
            LocalBatch: Batch of local tasks that have been executed.
        """
        if multiprocessing and cache_matrices:
            raise ValueError(
                "Cannot use multiprocessing and cache_matrices at the same time."
            )

        compile_options = dict(
            shots=shots,
            args=args,
            name=name,
            blockade_radius=blockade_radius,
            cache_matrices=cache_matrices,
            waveform_runtime=waveform_runtime,
        )

        solver_options = dict(
            multiprocessing=multiprocessing,
            num_workers=num_workers,
            solver_name=solver_name,
            atol=atol,
            rtol=rtol,
            nsteps=nsteps,
            interaction_picture=interaction_picture,
        )

        batch = self._compile(**compile_options)
        batch._run(**solver_options)

        return batch

    @beartype
    def __call__(
        self,
        *args: LiteralType,
        shots: int = 1,
        name: Optional[str] = None,
        blockade_radius: float = 0.0,
        waveform_runtime: str = "interpret",
        interaction_picture: bool = False,
        multiprocessing: bool = False,
        num_workers: Optional[int] = None,
        cache_matrices: bool = False,
        solver_name: str = "dop853",
        atol: float = 1e-7,
        rtol: float = 1e-14,
        nsteps: int = 2_147_483_647,
    ) -> LocalBatch:
        options = dict(
            shots=shots,
            args=args,
            name=name,
            blockade_radius=blockade_radius,
            waveform_runtime=waveform_runtime,
            multiprocessing=multiprocessing,
            num_workers=num_workers,
            cache_matrices=cache_matrices,
            solver_name=solver_name,
            atol=atol,
            rtol=rtol,
            nsteps=nsteps,
            interaction_picture=interaction_picture,
        )
        return self.run(**options)

    @beartype
    def run_callback(
        self,
        callback: Callable[[StateVector, NamedTuple, RydbergHamiltonian, Any], Any],
        program_args: Tuple[LiteralType, ...] = (),
        callback_args: Tuple = (),
        ignore_exceptions: bool = False,
        blockade_radius: float = 0.0,
        waveform_runtime: str = "interpret",
        interaction_picture: bool = False,
        cache_matrices: bool = False,
        multiprocessing: bool = False,
        num_workers: Optional[int] = None,
        solver_name: str = "dop853",
        atol: float = 1e-7,
        rtol: float = 1e-14,
        nsteps: int = 2_147_483_647,
        use_hyperfine: bool = False,
    ) -> List:
        """Run state-vector simulation with a callback to access full state-vector from
        emulator

        Args:
            callback (Callable[[StateVector, Metadata, RydbergHamiltonian, Any], Any]):
            The callback function to run for each task in batch. See note below for more
            details about the signature of the function.
            program_args (Tuple[LiteralType, ...], optional): The values for parameters
            defined in `args`. Defaults to ().
            callback_args (Tuple[Any,...], optional): Extra arguments to pass into
            ignore_exceptions: (bool, optional) If `True` any exception raised during
            a task will be saved instead of the resulting output of the callback,
            otherwise the first exception by task number will be raised after *all*
            tasks have executed. Defaults to False.
            blockade_radius (float, optional): Use the Blockade subspace given a
            particular radius. Defaults to 0.0.
            waveform_runtime: (str, optional): Specify which runtime to use for
            waveforms. Defaults to "interpret".
            interaction_picture (bool, optional): Use the interaction picture when
            solving schrodinger equation. Defaults to False.
            cache_matrices (bool, optional): Reuse previously evaluated matrcies when
            possible. Defaults to False.
            multiprocessing (bool, optional): Use multiple processes to process the
            batches. Defaults to False.
            num_workers (Optional[int], optional): Number of processes to run with
            multiprocessing. Defaults to None.
            solver_name (str, optional): Which SciPy Solver to use. Defaults to
            "dop853".
            atol (float, optional): Absolute tolerance for ODE solver. Defaults to
            1e-14.
            rtol (float, optional): Relative tolerance for adaptive step in ODE solver.
            Defaults to 1e-7.
            nsteps (int, optional): Maximum number of steps allowed per integration
            step. Defaults to 2_147_483_647, the maximum value.

        Returns:
            List: List of resulting outputs from the callbacks

        Raises:
            RuntimeError: Raises the first error that occurs, only if
            `ignore_exceptions=False`.

        Note:
            For the `callback` function, first argument is the many-body wavefunction
            as a 1D complex numpy array, the second argument is of type `Metadata` which
            is a Named Tuple where the fields correspond to the parameters of that given
            task, RydbergHamiltonian is the object that contains the Hamiltonian used to
            generate the evolution for that task, Finally any optional positional
            arguments are allowed after that. The return value can be anything, the
            results will be collected in a list for each task in the batch.


        """
        if multiprocessing:
            from multiprocessing import Process, Queue, cpu_count
        else:
            from queue import Queue

        if cache_matrices:
            compile_cache = CompileCache()
        else:
            compile_cache = None

        solver_args = dict(
            solver_name=solver_name,
            atol=atol,
            rtol=rtol,
            nsteps=nsteps,
            interaction_picture=interaction_picture,
        )

        runner = self.EmuRunner(
            compile_cache=compile_cache,
            solver_args=solver_args,
            callback=callback,
            callback_args=callback_args,
        )

        tasks = Queue()
        results = Queue()

        total_tasks = 0
        ir_iter = self._generate_ir(
            program_args, blockade_radius, waveform_runtime, use_hyperfine
        )
        for task_data in ir_iter:
            task_number = task_data.task_id
            emulator_ir = task_data.emulator_ir
            metadata = task_data.metadata_dict
            total_tasks += 1
            tasks.put((task_number, (emulator_ir, metadata)))

        workers = []
        if multiprocessing:
            num_workers = max(int(num_workers or cpu_count()), 1)
            num_workers = min(total_tasks, num_workers)

            for _ in range(num_workers):
                worker = Process(
                    target=BloqadePythonRoutine.process_tasks,
                    args=(runner, tasks, results),
                )
                worker.start()

                workers.append(worker)
        else:
            self.process_tasks(runner, tasks, results)

        # blocks until all
        # results have been fetched
        # from the id_results Queue
        id_results = []
        for i in range(total_tasks):
            id_results.append(results.get())

        if workers:
            for worker in workers:
                worker.join()

            tasks.close()
            results.close()

        id_results.sort(key=lambda x: x[0])
        results = []

        for task_id, result in id_results:
            if not ignore_exceptions and isinstance(result, BaseException):
                try:
                    raise result
                except BaseException:
                    raise RuntimeError(
                        f"{result.__class__.__name__} occured during child process "
                        f"running for task number {task_id}:\n{traceback.format_exc()}"
                    )

            results.append(result)

        return results

    def hamiltonian(
        self,
        *args: LiteralType,
        blockade_radius: float = 0.0,
        use_hyperfine: bool = False,
        waveform_runtime: str = "interpret",
        cache_matrices: bool = False,
    ) -> List[BloqadeEmulation]:
        """
        Generates a list of BloqadeEmulation objects which contain the Hamiltonian of your program.

        If you have a variable(s) in your program you have assigned multiple values via `batch_assign()`
        there will be multiple `BloqadeEmulation` objects, one for each value. On the other hand
        if the program only assumes a singular value per each variable, there will only be
        one `BloqadeEmulation` object but it will still be encapsulated in a list.


        Args:
            *args (LiteralType): If your program has a variable that was declared as run-time assignable
                via `.args` you may pass a value to it here. If there are multiple
                variables declared via `.args` the order in which you assign values to those variables
                through this argument should follow the order in which the declaration occurred.
            blockade_radius (float): The radius in which atoms blockade eachother. Default value is 0.0 micrometers.
            use_hyperfine (bool): Should the Hamiltonian account for hyperfine levels. Default value is False.
            waveform_runtime (str): Specify which runtime to use for waveforms. If "numba" is specify the waveform
                is compiled, otherwise it is interpreted via the "interpret" argument. Defaults to "interpret".
            cache_matrices (bool): Speed up Hamiltonian generation by reusing data (when possible) from previously generated Hamiltonians.
                Default value is False.

        Returns:
            List[BloqadeEmulation]

        """
        ir_iter = self._generate_ir(
            args, blockade_radius, waveform_runtime, use_hyperfine
        )

        if cache_matrices:
            compile_cache = CompileCache()
        else:
            compile_cache = None

        return [
            BloqadeEmulation(task_data, compile_cache=compile_cache)
            for task_data in ir_iter
        ]
