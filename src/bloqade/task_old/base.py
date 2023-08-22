from numbers import Number

from bloqade.submission.ir.task_results import QuEraTaskResults
from bloqade.submission.ir.parallel import ParallelDecoder

from typing import (
    TYPE_CHECKING,
    Dict,
    List,
    Tuple,
    Optional,
    TypeVar,
    Generic,
)
from collections import OrderedDict
from pydantic.dataclasses import dataclass


if TYPE_CHECKING:
    from bloqade.task.report import Report


@dataclass(frozen=True)
class Geometry:
    sites: List[Tuple[float, float]]
    filling: List[int]
    parallel_decoder: Optional[ParallelDecoder] = None


TaskSubType = TypeVar("TaskSubType", bound="Task")
TaskResultsSubType = TypeVar("TaskResultsSubType", bound="TaskResults")
BatchTaskSubType = TypeVar("BatchTaskSubType", bound="BatchTask")
BatchResultSubType = TypeVar("BatchResultSubType", bound="BatchResult")


# The reason why we do not simply pass objects up to the parent class is because
# I would like to preserve the ability to serialize the objects to JSON.


class TaskResults(Generic[TaskSubType]):
    def _task(self) -> TaskSubType:
        raise NotImplementedError(f"{self.__class__.__name__}._task() not implemented")

    @property
    def task(self) -> TaskSubType:
        return self._task()


class TaskShotResults(TaskResults[TaskSubType]):
    def _quera_task_result(self) -> QuEraTaskResults:
        raise NotImplementedError(
            f"{self.__class__.__name__}._quera_task_result() not implemented"
        )

    @property
    def quera_task_result(self) -> QuEraTaskResults:
        return self._quera_task_result()


class Task:
    def _geometry(self) -> Geometry:
        raise NotImplementedError(
            f"{self.__class__.__name__}._geometry() not implemented"
        )

    def _metadata(self) -> Dict[str, Number]:
        return {}

    @property
    def metadata(self) -> Dict[str, Number]:
        return self._metadata()

    @property
    def geometry(self) -> Geometry:
        return self._geometry()

    def submit(self: TaskSubType) -> TaskResults[TaskSubType]:
        raise NotImplementedError(f"{self.__class__.__name__}.submit() not implemented")


class BatchResult(Generic[TaskResultsSubType]):
    # fundamental interface, list of task results
    # each subclass implements a different way of getting the results
    # e.g. cloud, local, etc. this is the basic interface required by
    # he report object to construct the dataframe, etc.
    # Any Batch Result should at the very least implement this interface
    # Other subclasses will have additional methods for different use cases.

    def _task_results(
        self,
    ) -> OrderedDict[int, TaskResultsSubType]:
        raise NotImplementedError(
            f"{self.__class__.__name__}._task_results() not implemented"
        )

    @property
    def task_results(
        self,
    ) -> OrderedDict[int, TaskResultsSubType]:
        return self._task_results()

    def report(self) -> "Report":
        from bloqade.task.report import Report

        return Report(self)


class BatchTask(Generic[TaskSubType, BatchResultSubType]):
    def _tasks(self: BatchTaskSubType) -> OrderedDict[int, TaskSubType]:
        raise NotImplementedError(f"{self.__class__.__name__}._tasks() not implemented")

    @property
    def tasks(self) -> OrderedDict[int, TaskSubType]:
        return self._tasks()

    def submit(self) -> BatchResultSubType:
        raise NotImplementedError(f"{self.__class__.__name__}.submit() not implemented")
