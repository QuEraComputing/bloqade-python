from collections import OrderedDict
from .base import RoutineBase
from bloqade.task.batch import LocalBatch
from typing import Tuple
from numbers import Real
from dataclasses import dataclass


@dataclass(frozen=True)
class BloqadeServiceOptions(RoutineBase):
    def python(self):
        return BloqadePythonRoutine(source=self.source)


@dataclass(frozen=True)
class BloqadePythonRoutine(RoutineBase):
    def compile(
        self,
        shots: int,
        args: Tuple[Real, ...] = (),
        name: str | None = None,
        blockade_radius: float = 0.0,
        cache_matrices: bool = False,
    ) -> LocalBatch:
        from bloqade.codegen.common.assignment_scan import AssignmentScan
        from bloqade.codegen.common.assign_variables import AssignAnalogCircuit
        from bloqade.emulate.codegen.emulator_ir import EmulatorProgramCodeGen
        from bloqade.emulate.codegen.rydberg_hamiltonian import CompileCache
        from bloqade.task.bloqade import BloqadeTask

        circuit, params = self.source.parse_source()

        circuit = AssignAnalogCircuit(params.static_params).visit(circuit)

        if cache_matrices:
            matrix_cache = CompileCache()
        else:
            matrix_cache = None

        tasks = OrderedDict()
        for task_number, batch_param in enumerate(params.batch_assignments(*args)):
            record_params = AssignmentScan(batch_param).emit(circuit)
            final_circuit = AssignAnalogCircuit(record_params).visit(circuit)
            emulator_ir = EmulatorProgramCodeGen(blockade_radius=blockade_radius).emit(
                final_circuit
            )
            tasks[task_number] = BloqadeTask(shots, emulator_ir, matrix_cache)

        return LocalBatch(self.source, tasks, name)

    def run(
        self,
        shots: int,
        args: Tuple[Real, ...] = (),
        name: str | None = None,
        blockade_radius: float = 0.0,
        cache_matrices: bool = False,
        multiprocessing: bool = False,
        num_workers: int | None = None,
        solver_name: str = "dop853",
        atol: float = 1e-14,
        rtol: float = 1e-7,
        nsteps: int = 2_147_483_647,
    ):
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
        )

        batch = self.compile(**compile_options)
        batch._run(**solver_options)

        return batch

    def __call__(
        self,
        *args: Real,
        shots: int = 1,
        name: str | None = None,
        blockade_radius: float = 0.0,
        multiprocesing: bool = False,
        num_workers: int | None = None,
        cache_matrices: bool = False,
        solver_name: str = "dop853",
        atol: float = 1e-7,
        rtol: float = 1e-14,
        nsteps: int = 2_147_483_647,
    ):
        options = dict(
            shots=shots,
            args=args,
            name=name,
            blockade_radius=blockade_radius,
            multiprocesing=multiprocesing,
            num_workers=num_workers,
            cache_matrices=cache_matrices,
            solver_name=solver_name,
            atol=atol,
            rtol=rtol,
            nsteps=nsteps,
        )
        return self.run(**options)
