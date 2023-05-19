from bloqade.submission.quera_api_client.ir.task_results import QuEraTaskResults
from typing import List, Union, Optional
from numpy.typing import NDArray
from pandas import DataFrame


class Task:
    def submit(self) -> "TaskFuture":
        raise NotImplementedError


class TaskFuture:
    task_results: Optional[QuEraTaskResults]

    def report(self) -> "Report":
        """generate the task report"""
        raise NotImplementedError

    def fetch(self) -> QuEraTaskResults:
        raise NotImplementedError


class Batch:
    def submit(self) -> "BatchFuture":
        raise NotImplementedError


class BatchFuture:
    def report(self) -> "Report":
        raise NotImplementedError

    def fetch(self) -> List[QuEraTaskResults]:
        raise NotImplementedError


# NOTE: this is only the basic report, we should provide
#      a way to customize the report class,
#      e.g result.plot() returns a `TaskPlotReport` class instead
class Report:
    def __init__(self) -> None:
        self._dataframe = None  # df cache
        self._bitstring = None  # bitstring cache

    def construct_dataframe(self):
        raise NotImplementedError

    def construct_bitstring(self):
        raise NotImplementedError

    @property
    def dataframe(self) -> DataFrame:
        if self._dataframe:
            return self._dataframe

        self._dataframe = self.construct_dataframe()
        return self._dataframe

    @property
    def bitstring(self) -> NDArray:
        if self._bitstring:
            return self._bitstring
        self._bitstring = self.construct_bitstring()
        return self._bitstring

    @property
    def markdown(self) -> str:
        return self.dataframe.to_markdown()


class ShotReport(Report):
    def __init__(self, future) -> None:
        self._future = future
        self._perfect_filling = None
        super().__init__()

    def get_perfect_filling(self):
        raise NotImplementedError

    @property
    def future(self):
        return self._future

    @property
    def task_results(self) -> Union[List[QuEraTaskResults], QuEraTaskResults]:
        return self.future.task_results

    @property
    def perfect_filling(self):
        if self._perfect_filling:
            return self._perfect_filling

        self._perfect_filling = self.get_perfect_filling()
        return self._perfect_filling

    def construct_bitstring(self):
        return self.dataframe.loc[self.perfect_filling].to_numpy()

    def rydberg_densities(self):
        return self.dataframe.loc[self.perfect_filling].mean()
