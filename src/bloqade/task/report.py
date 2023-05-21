from pandas import DataFrame
import numpy as np
from bloqade.submission.ir.task_results import QuEraTaskResults
from typing import TYPE_CHECKING, List


if TYPE_CHECKING:
    from .base import TaskFuture, BatchFuture


# NOTE: this is only the basic report, we should provide
#      a way to customize the report class,
#      e.g result.plot() returns a `TaskPlotReport` class instead
class TaskReport:
    def __init__(self, result: "TaskFuture") -> None:
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
        return self.result.task_result_ir

    @property
    def markdown(self) -> str:
        return self.dataframe.to_markdown()


class BatchReport:
    def __init__(self, batch: "BatchFuture"):
        self.batch = batch
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
    def task_result(self) -> List[QuEraTaskResults]:
        return self.result.task_result_ir_list

    @property
    def markdown(self) -> str:
        return self.dataframe.to_markdown()
