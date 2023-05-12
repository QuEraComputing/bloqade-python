from pydantic import BaseModel
from quera_ahs_utils.quera_ir.task_results import QuEraTaskResults

from quera_ahs_utils.ir import quera_task_to_braket_ahs
from bloqade.submission.mock import DumbMockBackend
from bloqade.submission.quera import QuEraBackend
from bloqade.submission.braket import BraketBackend
from bloqade.submission.ir import (
    QuantumTaskIR,
    BraketTaskSpecification,
    QuEraTaskSpecification,
)

from bloqade.ir import Sequence
from typing import TYPE_CHECKING, Dict, Optional, Union, List
from numbers import Number

if TYPE_CHECKING:
    from .lattice.base import Lattice

from pandas import DataFrame
import numpy as np


class Task:
    def submit(self, token=None) -> "TaskResult":
        # TODO: do a real task result
        # 1. run the corresponding codegen
        # 2. submit the codegen to the backend
        # NOTE: this needs to be implemented separately for each backend
        #       class, e.g the `submit` method for BraketTask, QuEraTask,
        #       SimuTask
        raise NotImplementedError(f"No task backend found for {self.__class__}")


class HardwareTask(BaseModel, Task):
    task_ir: QuantumTaskIR


# NOTE: this will contain the schema object and the program object
#       after codegen happens.
class BraketTask(HardwareTask):
    def __init__(self, prog: "Program", nshots: int) -> None:
        from bloqade.codegen.quera_hardware import SchemaCodeGen

        quera_task_ir = SchemaCodeGen().emit(nshots, prog)
        braket_ahs_program, nshots = quera_task_to_braket_ahs(quera_task_ir)
        self.backend = BraketBackend()

        super().__init__(BraketTaskSpecification(nshots, braket_ahs_program.to_ir()))


class QuEraTask(HardwareTask):
    def __init__(self, *args, **kwargs) -> None:
        from bloqade.codegen.quera_hardware import SchemaCodeGen

        match args:
            case (Program() as prog, int(nshots)):
                task_ir = SchemaCodeGen().emit(nshots, prog)
                self.backend = QuEraBackend()
                super().__init__(task_ir)

            case QuEraTaskSpecification() as task_ir:
                super().__init__(task_ir=task_ir)

            case _:
                super().__init__(*args, **kwargs)


class MockTask(HardwareTask):
    def __init__(
        self, prog: "Program", nshots: int, state_file=".mock_state.txt"
    ) -> None:
        super().__init__(prog, nshots)
        from bloqade.codegen.quera_hardware import SchemaCodeGen

        task_ir = SchemaCodeGen().emit(nshots, prog)

        super().__init__(task_ir)

        self.backend = DumbMockBackend(state_file=state_file)

    def submit(self, *args, **kwargs) -> "MockTaskResult":
        task_id = self.backend.submit_task(self.task_ir)
        return MockTaskResult(self.task_ir, task_id, self.backend)


class SimuTask(Task):
    def __init__(self, prog: "Program", nshots: int) -> None:
        self.prog = prog
        self.nshots = nshots
        # custom config goes here


class TaskResult:
    def report(self) -> "TaskReport":
        """generate the task report"""
        return TaskReport(self)


class QuantumTaskResult(BaseModel, TaskResult):
    task_ir: QuantumTaskIR
    task_id: str


class MockTaskResult(BaseModel, TaskResult):
    def __init__(self, task_ir: QuantumTaskIR, task_id: str, backend: DumbMockBackend):
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
        lattice: Lattice,
        sequence: Sequence,
        assignments: Optional[Dict[str, Union[Number, List[Number]]]] = None,
    ):
        self._lattice = lattice
        self._sequence = sequence
        self._assignments = assignments

    @property
    def lattice(self):
        return self._lattice

    @property
    def sequence(self):
        return self._sequence

    @property
    def assignments(self):
        return self._assignments

    def braket(self, *args, **kwargs) -> BraketTask:
        return BraketTask(self, *args, **kwargs)

    def quera(self, *args, **kwargs) -> QuEraTask:
        return QuEraTask(self, *args, **kwargs)

    def simu(self, *args, **kwargs) -> SimuTask:
        return SimuTask(self, *args, **kwargs)

    def mock(self, nshots: int, state_file: str = ".mock_state.txt") -> MockTask:
        return MockTask(self, nshots, state_file=state_file)
