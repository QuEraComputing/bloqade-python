from pydantic import BaseModel, ValidationError
from quera_ahs_utils.quera_ir.task_results import QuEraTaskResults

from quera_ahs_utils.ir import quera_task_to_braket_ahs
from bloqade.submission.mock import DumbMockBackend

from bloqade.submission.quera import QuEraBackend
from bloqade.submission.braket import BraketBackend
from bloqade.submission.ir import BraketTaskSpecification
from quera_ahs_utils.quera_ir.task_specification import QuEraTaskSpecification

from bloqade.ir import Sequence
from typing import TYPE_CHECKING, Dict, Optional, Union, List, TextIO
from numbers import Number

if TYPE_CHECKING:
    from .lattice.base import Lattice
from pandas import DataFrame
import numpy as np
import os
import json


class TaskFuture:
    def report(self) -> "TaskReport":
        """generate the task report"""
        return TaskReport(self)


class QuantumTaskFuture(TaskFuture):
    def json(self, exclude_none=True, by_alias=True, **json_options):
        return super().json(
            exclude_none=exclude_none, by_alias=by_alias, **json_options
        )

    def write_json(
        self, filename_or_io: Union[str, TextIO], mode: str = "w", **json_options
    ):
        match filename_or_io:
            case str(filename):
                with open(filename, mode) as io:
                    io.write(self.json(**json_options))
            case _:
                filename_or_io.write(self.json(**json_options))

    def fetch(self) -> QuEraTaskResults:
        raise NotImplementedError

    @property
    def task_results(self) -> QuEraTaskResults:
        if self.task_result_ir is None:
            self.task_result_ir = self.fetch()

        return self.task_result_ir


class MockTaskFuture(BaseModel, QuantumTaskFuture):
    task_ir: QuEraTaskSpecification
    task_id: str
    backend: DumbMockBackend
    task_result_ir: Optional[QuEraTaskResults] = None

    def fetch(self):
        return self.backend.task_results(self.task_id)


class BraketTaskFuture(BaseModel, QuantumTaskFuture):
    task_ir: BraketTaskSpecification
    task_id: str
    backend: BraketBackend
    task_result_ir: Optional[QuEraTaskResults] = None

    def fetch(self):
        return self.backend.task_results(self.task_id)


class QuEraTaskFuture(BaseModel, QuantumTaskFuture):
    task_ir: QuEraTaskSpecification
    task_id: str
    backend: QuEraBackend
    task_result_ir: Optional[QuEraTaskResults] = None

    def fetch(self):
        return self.backend.task_results(self.task_id)


def read_future_from_json(
    filename_or_io: Union[str, TextIO]
) -> Union[QuantumTaskFuture, BraketTaskFuture, MockTaskFuture]:
    match filename_or_io:
        case str(filename):
            with open(filename, "r") as io:
                quantum_task_ir = json.load(io)

        case _:
            quantum_task_ir = json.load(filename_or_io)

    try:
        return QuEraTaskFuture(**quantum_task_ir)
    except ValidationError:
        pass

    try:
        return BraketTaskFuture(**quantum_task_ir)
    except ValidationError:
        pass

    try:
        return MockTaskFuture(**quantum_task_ir)
    except ValidationError:
        pass

    raise ValueError("Unable to parse JSON file to a task future.")


# NOTE: this is only the basic report, we should provide
#      a way to customize the report class,
#      e.g result.plot() returns a `TaskPlotReport` class instead
class TaskReport:
    def __init__(self, result: TaskFuture) -> None:
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
        lattice: Optional["Lattice"],
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

    def simu(self, *args, **kwargs):
        raise NotImplementedError

    def braket(self, nshots: int) -> BraketTaskFuture:
        from bloqade.codegen.quera_hardware import SchemaCodeGen

        quera_task_ir = SchemaCodeGen().emit(nshots, self)
        braket_ahs_program, nshots = quera_task_to_braket_ahs(quera_task_ir)
        task_ir = BraketTaskSpecification(
            nshots=nshots, program=braket_ahs_program.to_ir()
        )

        backend = BraketBackend()
        task_id = backend.submit_task(task_ir)

        return BraketTaskFuture(task_ir=task_ir, task_id=task_id, backend=backend)

    def quera(self, nshots: int, config_file: Optional[str] = None) -> QuEraTaskFuture:
        from bloqade.codegen.quera_hardware import SchemaCodeGen

        task_ir = SchemaCodeGen().emit(nshots, self)

        if config_file is None:
            path = os.path.dirname(__file__)
            api_config_file = os.path.join(
                path, "submission", "quera_api_client", "config", "dev_quera_api.json"
            )
            with open(api_config_file, "r") as io:
                api_config = json.load(io)

            backend = QuEraBackend(**api_config)

        task_id = backend.submit_task(task_ir)

        return QuEraTaskFuture(task_ir=task_ir, task_id=task_id, backend=backend)

    def mock(self, nshots: int, state_file: str = ".mock_state.txt") -> MockTaskFuture:
        from bloqade.codegen.quera_hardware import SchemaCodeGen

        task_ir = SchemaCodeGen().emit(nshots, self)
        backend = DumbMockBackend(state_file=state_file)

        task_id = backend.submit_task(task_ir)
        return MockTaskFuture(task_ir=task_ir, task_id=task_id, backend=backend)
