from pandas import DataFrame
import numpy as np
from bloqade.submission.quera_api_client.ir.task_results import QuEraTaskResults
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .base import TaskFuture


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
        return self.result.task_result

    @property
    def markdown(self) -> str:
        return self.dataframe.to_markdown()
