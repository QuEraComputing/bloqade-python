from collections import OrderedDict
import datetime
import json
import os
import sys
import numpy as np
import traceback

from pydantic import BaseModel
from typing import Optional, Union, TextIO, Type, TypeVar
from bloqade.submission.ir.task_results import QuEraTaskResults, QuEraTaskStatusCode

from bloqade.task.base import (
    Task,
    TaskShotResults,
    BatchTask,
    BatchResult,
)
from bloqade.submission.base import SubmissionBackend, ValidationError


JSONSubType = TypeVar("JSONSubType", bound="JSONInterface")
CloudBatchResultSubType = TypeVar("CloudBatchResultSubType", bound="CloudBatchResult")
CloudBatchTaskSubType = TypeVar("CloudBatchTaskSubType", bound="CloudBatchTask")
CloudTaskShotResultsSubType = TypeVar(
    "CloudTaskShotResultsSubType", bound="CloudTaskShotResults"
)
CloudTaskSubType = TypeVar("CloudTaskSubType", bound="CloudTask")


class JSONInterface(BaseModel):
    def json(self, exclude_none=True, by_alias=True, **json_options) -> str:
        return super().json(
            exclude_none=exclude_none, by_alias=by_alias, **json_options
        )

    def save_json(
        self, filename_or_io: Union[str, TextIO], mode="w", **json_options
    ) -> None:
        if isinstance(filename_or_io, str):
            with open(filename_or_io, mode) as f:
                f.write(self.json(**json_options))
        else:
            filename_or_io.write(self.json(**json_options))

    @classmethod
    def load_json(
        cls: Type[JSONSubType], filename_or_io: Union[str, TextIO]
    ) -> JSONSubType:
        if isinstance(filename_or_io, str):
            with open(filename_or_io, "r") as f:
                params = json.load(f)
        else:
            params = json.load(filename_or_io)

        return cls(**params)


class CloudTaskShotResults(JSONInterface, TaskShotResults[CloudTaskSubType]):
    task_id: Optional[str]
    # CloudTaskShotResult is a TaskShotResult but acts like a future object.

    def _quera_task_result(self) -> QuEraTaskResults:
        return self.fetch_task_result(cache_result=True)

    def fetch_task_result(self, cache_result=False) -> QuEraTaskResults:
        raise NotImplementedError(
            f"{self.__class__.__name__}.fetch_task_result() not implemented"
        )

    def status(self) -> QuEraTaskStatusCode:
        raise NotImplementedError(f"{self.__class__.__name__}.status() not implemented")

    def cancel(self) -> None:
        raise NotImplementedError(f"{self.__class__.__name__}.cancel() not implemented")

    def resubmit_if_failed(
        self: CloudTaskShotResultsSubType,
    ) -> CloudTaskShotResultsSubType:
        if self.task_id and self.status() not in [
            QuEraTaskStatusCode.Failed,
            QuEraTaskStatusCode.Unaccepted,
        ]:
            return self
        else:
            return self.task.submit()


class CloudTask(JSONInterface, Task):
    def _backend(self) -> SubmissionBackend:
        raise NotImplementedError(
            f"{self.__class__.__name__}._backend() not implemented"
        )

    @property
    def backend(self) -> SubmissionBackend:
        """The backend that is used to call the web-API."""
        return self._backend()

    def run_validation(self) -> str:
        raise NotImplementedError(
            f"{self.__class__.__name__}.run_validation() not implemented"
        )

    def submit_no_task_id(
        self: CloudTaskSubType,
    ) -> CloudTaskShotResults[CloudTaskSubType]:
        raise NotImplementedError(
            f"{self.__class__.__name__}.submit_no_task_id() not implemented"
        )


class CloudBatchResult(JSONInterface, BatchResult[CloudTaskShotResultsSubType]):
    name: Optional[str] = None

    @classmethod
    def create_batch_result(
        cls: Type[CloudBatchResultSubType],
        ordered_dict: OrderedDict[int, CloudTaskShotResultsSubType],
        name: Optional[str] = None,
    ) -> CloudBatchResultSubType:
        raise NotImplementedError(
            f"{cls.__name__}.create_batch_result(cloud_task_results) not implemented."
        )

    def resubmit_failed_tasks(self: CloudBatchResultSubType) -> CloudBatchResultSubType:
        new_task_results = OrderedDict()
        for task_number, cloud_task_result in self.task_results.items():
            new_task_results[task_number] = cloud_task_result.resubmit_if_failed()

        return self.create_batch_result(new_task_results, name=self.name)

    def removing_failed_tasks(self: CloudBatchResultSubType) -> CloudBatchResultSubType:
        new_results = OrderedDict()
        for task_number, cloud_task_result in self.task_results.items():
            if cloud_task_result.status() in [
                QuEraTaskStatusCode.Failed,
                QuEraTaskStatusCode.Unaccepted,
            ]:
                continue

            new_results[task_number] = cloud_task_result

        return self.create_batch_result(new_results, self.name)

    def cancel(self) -> None:
        for task_result in self.task_results.values():
            task_result.cancel()

    def fetch_remote_results(self) -> None:
        for task_result in self.task_results.values():
            task_result.fetch_task_result(cache_result=True)


class CloudBatchTask(
    JSONInterface, BatchTask[CloudTaskSubType, CloudBatchResultSubType]
):
    name: Optional[str] = None

    class SubmissionException(Exception):
        pass

    @classmethod
    def create_batch_task(
        cls: Type[CloudBatchTaskSubType],
        tasks: OrderedDict[int, CloudTaskSubType],
        name: Optional[str] = None,
    ) -> CloudBatchTaskSubType:
        raise NotImplementedError(f"{cls.__name__}.create_batch_task() not implemented")

    def _batch_result_type(self) -> CloudBatchResultSubType:
        raise NotImplementedError(
            f"{self.__class__.__name__}._batch_result_type() not implemented"
        )

    @property
    def BatchResultType(self) -> Type[CloudBatchResultSubType]:
        return self._batch_result_type()

    def remove_invalid_tasks(self: CloudBatchTaskSubType) -> CloudBatchTaskSubType:
        new_tasks = OrderedDict()
        for task_number, task in self.tasks.items():
            try:
                task.run_validation()
                new_tasks[task_number] = task
            except ValidationError:
                continue

        return self.create_batch_task(new_tasks, name=self.name)

    def submit(self, shuffle_submit_order: bool = True) -> CloudBatchResultSubType:
        if shuffle_submit_order:
            submission_order = np.random.permutation(list(self.tasks.keys()))
        else:
            submission_order = list(self.tasks.keys())

        for task in self.tasks.values():
            try:
                task.run_validation()
            except NotImplementedError:
                break

        # submit tasks in random order but store them
        # in the original order of tasks.
        futures = OrderedDict()
        errors = OrderedDict()
        for task_index in submission_order:
            task = self.tasks[task_index]
            try:
                futures[task_index] = task.submit()
            except BaseException as error:
                # Create future object without the task id
                futures[task_index] = task.submit_no_task_id()
                # record the error in the error dict
                errors[int(task_index)] = {
                    "exception_type": error.__class__.__name__,
                    "stack trace": traceback.format_exc(),
                }

        cloud_batch_result = self.BatchResultType.create_batch_result(
            futures, name=self.name
        )
        if errors:
            time_stamp = datetime.datetime.now()

            if "win" in sys.platform:
                time_stamp = str(time_stamp).replace(":", "~")

            if self.name:
                future_file = f"{self.name}-partial-batch-future-{time_stamp}.json"
                error_file = f"{self.name}-partial-batch-errors-{time_stamp}.json"
            else:
                future_file = f"partial-batch-future-{time_stamp}.json"
                error_file = f"partial-batch-errors-{time_stamp}.json"

            cwd = os.get_cwd()
            cloud_batch_result.save_json(future_file, indent=2)

            with open(error_file, "w") as f:
                json.dump(errors, f, indent=2)

            raise CloudBatchTask.SubmissionException(
                "One or more error(s) occured during submission, please see "
                "the following files for more information:\n"
                f"  - {os.path.join(cwd, future_file)}\n"
                f"  - {os.path.join(cwd, error_file)}\n"
            )

        else:
            # TODO: think about if we should automatically save successful submissions
            #       as well.
            pass

        return cloud_batch_result
