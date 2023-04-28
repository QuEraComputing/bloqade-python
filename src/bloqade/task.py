# we have to put these objects in one file because of circular imports
# TODO: figure out how to remove the circular imports & split the file

from .ir.prelude import *
from pandas import DataFrame
import numpy as np

class Task:

    def __init__(self, prog: "Program", nshots: int) -> None:
        self.prog = prog
        self.nshtos = nshots

    def submit(self, token=None) -> "TaskResult":
        # TODO: do a real task result
        # 1. run the corresponding codegen
        # 2. submit the codegen to the backend
        # NOTE: this needs to be implemented separately for each backend
        #       class, e.g the `submit` method for BraketTask, QuEraTask,
        #       SimuTask
        return TaskResult()

class BraketTask(Task):
    
    def __init__(self, prog: "Program", nshots: int) -> None:
        super().__init__(prog, nshots)
        # custom config goes here

class QuEraTask(Task):
    
    def __init__(self, prog: "Program", nshots: int) -> None:
        super().__init__(prog, nshots)
        # custom config goes here

class SimuTask(Task):
    
    def __init__(self, prog: "Program", nshots: int) -> None:
        super().__init__(prog, nshots)
        # custom config goes here

class TaskResult:

    def report(self) -> "TaskReport":
        """generate the task report
        """
        return TaskReport(self)


# NOTE: this is only the basic report, we should provide
#      a way to customize the report class, 
#      e.g result.plot() returns a `TaskPlotReport` class instead

class TaskReport:

    def __init__(self, result: TaskResult) -> None:
        self.result = result
        self._dataframe = None # df cache
        self._bitstring = None # bitstring cache

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
