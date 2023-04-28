# we have to put these objects in one file because of circular imports
from .ir.prelude import *
from pandas import DataFrame

class Task:

    def __init__(self, prog: "Program", nshots: int) -> None:
        self.prog = prog
        self.nshtos = nshots

    def submit(self, token=None) -> "TaskResult":
        # TODO: do a real task result
        return TaskResult()

class BraketTask(Task):
    
    def __init__(self, prog: "Program", nshots: int) -> None:
        super().__init__(prog, nshots)
        # custom config goes here

class QuEraTask(Task):
    
    def __init__(self, prog: "Program", nshots: int) -> None:
        super().__init__(prog, nshots)
        # custom config goes here

class TaskResult:

    def report(self) -> "TaskReport":
        """generate the task report
        """
        return TaskReport(self)


class TaskReport:

    def __init__(self, result: TaskResult) -> None:
        self.result = result
        self._dataframe = None # df cache

    @property
    def dataframe(self) -> DataFrame:
        if self._dataframe:
            return self._dataframe
        self._dataframe = DataFrame()
        return self._dataframe


class Program:

    def __init__(self, lattice: "Lattice", seq: Sequence) -> None:
        self.latice = lattice
        self.seq = seq

    def braket(self, *args, **kwargs) -> BraketTask:
        return BraketTask(self, *args, **kwargs)

    def quera(self, nshots: int) -> QuEraTask:
        pass
