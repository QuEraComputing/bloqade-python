from collections import OrderedDict, namedtuple
from decimal import Decimal

from bloqade.ir.routine.base import RoutineBase, __pydantic_dataclass_config__
from bloqade.builder.typing import LiteralType
from bloqade.task.batch import LocalBatch
from beartype import beartype
from beartype.typing import Optional, Tuple, Callable, Dict, Any, List
from pydantic.dataclasses import dataclass
import numpy as np

from bloqade.emulate.codegen.hamiltonian import CompileCache, RydbergHamiltonianCodeGen
from bloqade.emulate.ir.state_vector import AnalogGate

from multiprocessing import Process, Queue, cpu_count


@dataclass(frozen=True, config=__pydantic_dataclass_config__)
class BloqadeServiceOptions(RoutineBase):
    def python(self):
        return BloqadePythonRoutine(self.source, self.circuit, self.params)


@dataclass(frozen=True, config=__pydantic_dataclass_config__)
class BloqadePythonRoutine(RoutineBase):
    @staticmethod
    def process_tasks(tasks, results, runner):
        while not tasks.empty():
            task_id, (emulator_ir, metadata) = tasks.get()
            result = runner.run_task(emulator_ir, metadata)
            results.put((task_id, result))

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

            metadata = MetaData(**{k: float(v) for k, v in metadata_dict.items()})

            zero_state = hamiltonian.space.zero_state(np.complex128)
            (register,) = AnalogGate(hamiltonian).apply(zero_state, **self.solver_args)

            return self.callback(register, metadata, hamiltonian, *self.callback_args)

    def _generate_ir(self, args, blockade_radius):
        from bloqade.ir.analysis.assignment_scan import AssignmentScan
        from bloqade.codegen.common.assign_variables import AssignAnalogCircuit
        from bloqade.codegen.emulator_ir import EmulatorProgramCodeGen

        circuit, params = self.circuit, self.params

        circuit = AssignAnalogCircuit(params.static_params).visit(circuit)

        for task_number, batch_param in enumerate(params.batch_assignments(*args)):
            record_params = AssignmentScan(batch_param).emit(circuit)
            final_circuit = AssignAnalogCircuit(record_params).visit(circuit)
            metadata = {**params.static_params, **record_params}
            emulator_ir = EmulatorProgramCodeGen(blockade_radius=blockade_radius).emit(
                final_circuit
            )
            yield task_number, emulator_ir, metadata

    def _compile(
        self,
        shots: int,
        args: Tuple[LiteralType, ...] = (),
        name: Optional[str] = None,
        blockade_radius: LiteralType = 0.0,
        cache_matrices: bool = False,
    ) -> LocalBatch:
        from bloqade.task.bloqade import BloqadeTask

        if cache_matrices:
            matrix_cache = CompileCache()
        else:
            matrix_cache = None

        tasks = OrderedDict()
        it_iter = self._generate_ir(args, blockade_radius)
        for task_number, emulator_ir, metadata in it_iter:
            tasks[task_number] = BloqadeTask(shots, emulator_ir, metadata, matrix_cache)

        return LocalBatch(self.source, tasks, name)

    @beartype
    def run(
        self,
        shots: int,
        args: Tuple[LiteralType, ...] = (),
        name: Optional[str] = None,
        blockade_radius: float = 0.0,
        interaction_picture: bool = False,
        cache_matrices: bool = False,
        multiprocessing: bool = False,
        num_workers: Optional[int] = None,
        solver_name: str = "dop853",
        atol: float = 1e-14,
        rtol: float = 1e-7,
        nsteps: int = 2_147_483_647,
    ) -> LocalBatch:
        """Run the current program using bloqade python backend

        Args:
            shots (int): number of shots after running state vector simulation
            args (Tuple[Real, ...], optional): The values for parameters defined
            in `args`. Defaults to ().
            name (Optional[str], optional): Name to give this run. Defaults to None.
            blockade_radius (float, optional): Use the Blockade subspace given a
            particular radius. Defaults to 0.0.
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
        callback: Callable[[np.ndarray, Dict[str, Decimal], Any], Any],
        program_args: Tuple[LiteralType, ...] = (),
        callback_args: Tuple = (),
        blockade_radius: float = 0.0,
        interaction_picture: bool = False,
        cache_matrices: bool = False,
        multiprocessing: bool = False,
        num_workers: Optional[int] = None,
        solver_name: str = "dop853",
        atol: float = 1e-14,
        rtol: float = 1e-7,
        nsteps: int = 2_147_483_647,
    ) -> List:
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
        it_iter = self._generate_ir(program_args, blockade_radius)
        for task_number, emulator_ir, metadata in it_iter:
            total_tasks += 1
            tasks.put((task_number, (emulator_ir, metadata)))

        workers = []
        if multiprocessing:
            num_workers = max(int(num_workers or cpu_count()), 1)

            for _ in range(num_workers):
                worker = Process(
                    target=BloqadePythonRoutine.process_tasks,
                    args=(tasks, results, runner),
                )
                worker.start()

                workers.append(worker)
        else:
            while not tasks.empty():
                task_id, (emulator_ir, metadata) = tasks.get()
                result = runner.run_task(emulator_ir, metadata)
                results.put((task_id, result))

        # blocks until all
        # results have been fetched
        # from the id_results Queue
        id_results = []
        for i in range(total_tasks):
            id_results.append(results.get())

        for worker in workers:
            worker.join()

        tasks.close()
        results.close()

        id_results.sort(key=lambda x: x[0])
        results = [result for _, result in id_results]

        return results
