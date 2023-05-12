from pydantic import BaseModel
from quera_ahs_utils.quera_ir.task_results import QuEraTaskResults

from quera_ahs_utils.ir import quera_task_to_braket_ahs
from bloqade.submission.mock import DumbMockBackend

from bloqade.submission.quera import QuEraBackend
from bloqade.submission.braket import BraketBackend
from bloqade.submission.ir import (
    QuantumTaskIR,
    BraketTaskSpecification,
)

from bloqade.ir import Sequence
from typing import TYPE_CHECKING, Dict, Optional, Union, List
from numbers import Number

if TYPE_CHECKING:
    from .lattice.base import Lattice

from pandas import DataFrame
import numpy as np
import os
import json


class Task:
    def submit(self, session=None) -> "TaskResult":
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
    backend: BraketBackend = BraketBackend()

    def submit(self) -> "TaskResult":
        task_id = self.backend.submit_task(self.task_ir)
        return BraketTaskResult(
            task_ir=self.task_ir, task_id=task_id, backend=self.backend
        )


class QuEraTask(HardwareTask):
    backend: QuEraBackend

    def submit(self) -> "QuEraTaskResult":
        task_id = self.backend.submit_task(self.task_ir)
        return QuEraTaskResult(
            task_ir=self.task_ir, task_id=task_id, backend=self.backend
        )


class MockTask(HardwareTask):
    backend: DumbMockBackend

    def submit(self) -> "MockTaskResult":
        task_id = self.backend.submit_task(self.task_ir)
        return MockTaskResult(
            task_ir=self.task_ir, task_id=task_id, backend=self.backend
        )


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
    task_result_ir: Optional[QuEraTaskResults] = None

    def json(self, exclude_none=True, by_alias=True, **options):
        return super().json(exclude_none=exclude_none, by_alias=by_alias, **options)

    @property
    def task_results(self) -> QuEraTaskResults:
        raise NotImplementedError


class MockTaskResult(QuantumTaskResult):
    backend: DumbMockBackend

    @property
    def task_results(self) -> QuEraTaskResults:
        if self.task_result_ir is None:
            self.task_result_ir = self.backend.task_results(self.task_id)

        return self.task_result_ir


class BraketTaskResult(QuantumTaskResult):
    backend: BraketBackend

    @property
    def task_results(self) -> QuEraTaskResults:
        if self.task_result_ir is None:
            self.task_result_ir = self.backend.task_results(self.task_id)

        return self.task_result_ir


class QuEraTaskResult(QuantumTaskResult):
    backend: QuEraBackend

    @property
    def task_results(self) -> QuEraTaskResults:
        if self.task_result_ir is None:
            self.task_result_ir = self.backend.task_results(self.task_id)

        return self.task_result_ir


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
    def task_result(self) -> QuEraTaskResults:
        return self.result.task_result

    @property
    def markdown(self) -> str:
        return self.dataframe.to_markdown()


# NOTE: this is just a dummy type bundle geometry and sequence
#       information together and forward them to backends.
class Program:
    def __init__(
        self,
        lattice: "Lattice",
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

    def simu(self, *args, **kwargs) -> SimuTask:
        raise NotImplementedError

    def braket(self, nshots: int) -> BraketTask:
        from bloqade.codegen.quera_hardware import SchemaCodeGen

        quera_task_ir = SchemaCodeGen().emit(nshots, self)
        braket_ahs_program, nshots = quera_task_to_braket_ahs(quera_task_ir)
        task_ir = BraketTaskSpecification(
            nshots=nshots, program=braket_ahs_program.to_ir()
        )

        return BraketTask(task_ir=task_ir)

    def quera(self, nshots: int, config_file: Optional[str] = None) -> QuEraTask:
        from bloqade.codegen.quera_hardware import SchemaCodeGen

        task_ir = SchemaCodeGen().emit(nshots, self)

        if config_file is None:
            path = os.path.dirname(__file__)
            api_config_file = os.path.join(
                path, "submission", "config", "dev_quera_api.json"
            )
            with open(api_config_file, "r") as io:
                api_config = json.load(io)

            backend = QuEraBackend(**api_config)

        return QuEraTask(task_ir=task_ir, backend=backend)

    def mock(self, nshots: int, state_file: str = ".mock_state.txt") -> MockTask:
        from bloqade.codegen.quera_hardware import SchemaCodeGen

        task_ir = SchemaCodeGen().emit(nshots, self)
        backend = DumbMockBackend(state_file=state_file)

        return MockTask(task_ir=task_ir, backend=backend)
