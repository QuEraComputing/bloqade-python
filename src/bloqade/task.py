from quera_ahs_utils.quera_ir.task_results import QuEraTaskResults

from bloqade.submission.mock_backend import DumbMockBackend
from .ir import Sequence, Variable, Literal
from typing import TYPE_CHECKING, Dict, Union

if TYPE_CHECKING:
    from .lattice.base import Lattice

from pandas import DataFrame
import numpy as np


class Task:
    def __init__(self, prog: "Program", nshots: int) -> None:
        self.prog = prog
        self.nshots = nshots

    def submit(self, token=None) -> "TaskResult":
        # TODO: do a real task result
        # 1. run the corresponding codegen
        # 2. submit the codegen to the backend
        # NOTE: this needs to be implemented separately for each backend
        #       class, e.g the `submit` method for BraketTask, QuEraTask,
        #       SimuTask
        raise NotImplementedError(f"No task backend found for {self.__class__}")


# NOTE: this will contain the schema object and the program object
#       after codegen happens.
class BraketTask(Task):
    def __init__(self, prog: "Program", nshots: int) -> None:
        super().__init__(prog, nshots)
        # quera_task = QuEraTaskSpecification(
        #     nshots=self.nshots,
        #     lattice=LatticeCodeGen(assignments=self.prog.assignments).emit(
        #         self.prog.lattice
        #     ),
        #     effective_hamiltonian=SequenceCodeGen(
        #         n_atoms=self.prog.lattice.n_atoms,
        #         assignments=self.prog.assignments,
        #     ).emit(self.prog.seq),
        # )
        # _, braket_task = quera_task_to_braket_ahs(quera_task)
        # self.task_ir = braket_task.to_ir()

    def submit(self, token=None) -> "TaskResult":
        return TaskResult()


class QuEraTask(Task):
    def __init__(self, prog: "Program", nshots: int) -> None:
        super().__init__(prog, nshots)
        # self.task_ir = QuEraTaskSpecification(
        #     nshots=self.nshots,
        #     lattice=LatticeCodeGen(assignments=self.prog.assignments).emit(
        #         self.prog.lattice
        #     ),
        #     effective_hamiltonian=SequenceCodeGen(
        #         n_atoms=self.prog.lattice.n_atoms,
        #         assignments=self.prog.assignments,
        #     ).emit(self.prog.seq),
        # )


class MockTask(Task):
    def __init__(
        self, prog: "Program", nshots: int, state_file=".mock_state.txt"
    ) -> None:
        super().__init__(prog, nshots)

        from bloqade.codegen.quera_hardware import SchemaCodeGen

        self.backend = DumbMockBackend(state_file=state_file)
        self.task_ir = SchemaCodeGen().emit(nshots, prog)

    def submit(self, *args, **kwargs) -> "MockTaskResult":
        return MockTaskResult(self.backend.submit_task(self.task_ir), self.backend)


class SimuTask(Task):
    def __init__(self, prog: "Program", nshots: int) -> None:
        super().__init__(prog, nshots)
        # custom config goes here


class TaskResult:
    def report(self) -> "TaskReport":
        """generate the task report"""
        return TaskReport(self)


class MockTaskResult(TaskResult):
    def __init__(self, task_id: str, backend: DumbMockBackend):
        self.task_id = task_id
        self.backend = backend
        self._task_result_ir = None

    @property
    def task_result_ir(self) -> QuEraTaskResults:
        if not self._task_result_ir:
            self._task_result_ir = self.backend.task_results(self.task_id)

        return self._task_result_ir


# NOTE: this is only the basic report, we should provide
#      a way to customize the report class,
#      e.g result.plot() returns a `TaskPlotReport` class instead


class TaskReport:
    def __init__(self, result: TaskResult) -> None:
        self.result = result
        self._dataframe = None  # df cache
        self._bitstring = None  # bitstring cache

    @property
    def dataframe(self) -> DataFrame:
        if self._dataframe:
            return self._dataframe
        self._dataframe = DataFrame()
        return self._dataframe

    @property
    def bitstring(self) -> np.array:
        if self._bitstring:
            return self._bitstring
        self._bitstring = np.array([])
        return self._bitstring

    @property
    def task_result_ir(self) -> QuEraTaskResults:
        return self.result.task_result_ir

    @property
    def markdown(self) -> str:
        return self.dataframe.to_markdown()


# NOTE: this is just a dummy type bundle geometry and sequence
#       information together and forward them to backends.
class Program:
    def __init__(
        self,
        lattice: Union[None, "Lattice"],
        seq: Sequence,
        assignments: Union[None, Dict[Variable, Literal]] = None,
    ) -> None:
        self.lattice = lattice
        self.seq = seq
        self.assignments = assignments

    def braket(self, *args, **kwargs) -> BraketTask:
        return BraketTask(self, *args, **kwargs)

    def quera(self, *args, **kwargs) -> QuEraTask:
        return QuEraTask(self, *args, **kwargs)

    def simu(self, *args, **kwargs) -> SimuTask:
        return SimuTask(self, *args, **kwargs)

    def mock(self, nshots: int, state_file: str = ".mock_state.txt") -> MockTask:
        return MockTask(self, nshots, state_file=state_file)
