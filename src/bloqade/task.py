# we have to put these objects in one file because of circular imports
# TODO: figure out how to remove the circular imports & split the file

from quera_ahs_utils.quera_ir.task_specification import QuEraTaskSpecification
from quera_ahs_utils.ir import quera_task_to_braket_ahs

from bloqade.codegen.hardware.sequence import SequenceCodeGen
from bloqade.codegen.hardware.lattice import LatticeCodeGen

from .ir.prelude import *
from typing import TYPE_CHECKING

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
        return TaskResult()


# NOTE: this will contain the schema object and the program object
#       after codegen happens.
class BraketTask(Task):
    def __init__(self, prog: "Program", nshots: int) -> None:
        super().__init__(prog, nshots)
        quera_task = QuEraTaskSpecification(
            nshots=self.nshots,
            lattice=LatticeCodeGen(ariable_reference=self.prog.variable_reference).emit(
                self.lattice
            ),
            effective_hamiltonian=SequenceCodeGen(
                n_atoms=self.lattice.n_atoms,
                variable_reference=self.prog.variable_reference,
            ).emit(self.prog.seq),
        )
        _, braket_task = quera_task_to_braket_ahs(quera_task)
        self.task_ir = braket_task.to_ir()


class QuEraTask(Task):
    def __init__(self, prog: "Program", nshots: int) -> None:
        super().__init__(prog, nshots)
        self.task_ir = QuEraTaskSpecification(
            nshots=self.nshots,
            lattice=LatticeCodeGen(ariable_reference=self.prog.variable_reference).emit(
                self.lattice
            ),
            effective_hamiltonian=SequenceCodeGen(
                n_atoms=self.lattice.n_atoms,
                variable_reference=self.prog.variable_reference,
            ).emit(self.prog.seq),
        )


class SimuTask(Task):
    def __init__(self, prog: "Program", nshots: int) -> None:
        super().__init__(prog, nshots)
        # custom config goes here


class TaskResult:
    def report(self) -> "TaskReport":
        """generate the task report"""
        return TaskReport(self)


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
    def markdown(self) -> str:
        return self.dataframe.to_markdown()


# NOTE: this is just a dummy type bundle geometry and sequence
#       information together and forward them to backends.
class Program:
    def __init__(self, lattice: "Lattice", seq: Sequence) -> None:
        self.latice = lattice
        self.seq = seq

    def braket(self, *args, **kwargs) -> BraketTask:
        return BraketTask(self, *args, **kwargs)

    def quera(self, *args, **kwargs) -> QuEraTask:
        return QuEraTask(self, *args, **kwargs)

    def simu(self, *args, **kwargs) -> SimuTask:
        return SimuTask(self, *args, **kwargs)
