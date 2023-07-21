from numbers import Number

from bloqade.submission.ir.task_results import QuEraTaskResults
from bloqade.submission.ir.parallel import ParallelDecoder

from typing import TYPE_CHECKING, Dict, List, Tuple, Optional, Union, Type, TypeVar
from collections import OrderedDict
from pydantic.dataclasses import dataclass


if TYPE_CHECKING:
    from bloqade.task.cloud_base import CloudTask, CloudTaskShotResult
    from bloqade.task.report import Report


@dataclass(frozen=True)
class Geometry:
    sites: List[Tuple[float, float]]
    filling: List[int]
    parallel_decoder: Optional[ParallelDecoder]


TaskSubType = TypeVar("TaskSubType", bound="Task")
TaskShotResultSubType = TypeVar("TaskShotResultSubType", bound="TaskShotResult")
BatchTaskSubType = TypeVar("BatchTaskSubType", bound="BatchTask")
BatchResultSubType = TypeVar("BatchResultSubType", bound="BatchResult")


# The reason why we do not simply pass objects up to the parent class is because
# I would like to preserve the ability to serialize the objects to JSON.


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

    def submit(self) -> Union["TaskShotResult", "CloudTaskShotResult"]:
        raise NotImplementedError(f"{self.__class__.__name__}.submit() not implemented")


class TaskShotResult:
    def _task(self) -> Union[Task, "CloudTask"]:
        raise NotImplementedError(f"{self.__class__.__name__}._task() not implemented")

    def _quera_task_result(self) -> QuEraTaskResults:
        raise NotImplementedError(
            f"{self.__class__.__name__}._quera_task_result() not implemented"
        )

    @property
    def task(self) -> Union[Task, "CloudTask"]:
        return self._task()

    @property
    def quera_task_result(self) -> QuEraTaskResults:
        return self._quera_task_result()


class BatchTask:
    def _tasks(self) -> OrderedDict[int, Union[Task, "CloudTask"]]:
        raise NotImplementedError(f"{self.__class__.__name__}._tasks() not implemented")

    @property
    def tasks(self) -> OrderedDict[int, Union[Task, "CloudTask"]]:
        return self._tasks()

    def submit(self) -> "BatchResult":
        raise NotImplementedError(f"{self.__class__.__name__}.submit() not implemented")


class BatchResult:
    # fundamental interface, list of task results
    # each subclass implements a different way of getting the results
    # e.g. cloud, local, etc. this is the basic interface required by
    # he report object to construct the dataframe, etc.
    # Any Batch Result should at the very least implement this interface
    # Other subclasses will have additional methods for different use cases.

    @classmethod
    def create_batch_result(
        cls: Type[BatchResultSubType],
        ordered_dict: OrderedDict[int, Union[TaskShotResult, "CloudTaskShotResult"]],
    ) -> BatchResultSubType:
        raise NotImplementedError(
            f"{cls.__name__}.from_ordered_dict(ordered_dict: ) not implemented."
        )

    def _task_results(
        self,
    ) -> OrderedDict[int, Union[TaskShotResult, "CloudTaskShotResult"]]:
        raise NotImplementedError(
            f"{self.__class__.__name__}._task_results() not implemented"
        )

    @property
    def task_results(
        self,
    ) -> OrderedDict[int, Union[TaskShotResult, "CloudTaskShotResult"]]:
        return self._task_results()

    def report(self) -> "Report":
        from bloqade.task.report import Report

        return Report(self)
