from pydantic import BaseModel
from bloqade.submission.ir.task_results import QuEraTaskResults
from bloqade.submission.mock import DumbMockBackend
from bloqade.submission.quera import QuEraBackend
from bloqade.submission.braket import BraketBackend
from bloqade.submission.ir.braket import BraketTaskSpecification, to_braket_task_ir
from bloqade.submission.ir.task_specification import (
    QuEraTaskSpecification,
)
from bloqade.submission.ir.parallel import ParallelDecoder
from bloqade.submission.ir.task_results import QuEraTaskStatusCode

from .base import Task, TaskFuture, Future, Job

from typing import Optional, List

import numpy as np


class MockTask(BaseModel, Task):
    parallel_decoder: Optional[ParallelDecoder]
    mock_backend: Optional[DumbMockBackend]
    mock_task_ir: Optional[QuEraTaskSpecification]

    def submit(self):
        if self.mock_backend:
            task_id = self.mock_backend.submit_task(self.mock_task_ir)
            return HardwareTaskFuture(
                task_id=task_id,
                mock_backend=self.mock_backend,
                mock_task_ir=self.mock_task_ir,
                parallel_decoder=self.parallel_decoder,
            )
        return super().submit()

    def run_validation(self) -> None:
        if self.mock_backend:
            self.mock_backend.validate(self.mock_task_ir)

        super().run_validation()


class BraketTask(MockTask):
    braket_backend: Optional[BraketBackend]
    braket_task_ir: Optional[BraketTaskSpecification]

    def submit(self):
        if self.braket_backend:
            task_id = self.braket_backend.submit_task(self.braket_task_ir)
            return HardwareTaskFuture(
                task_id=task_id,
                braket_backend=self.braket_backend,
                braket_task_ir=self.braket_task_ir,
                parallel_decoder=self.parallel_decoder,
            )
        return super().submit()

    def run_validation(self) -> None:
        if self.braket_backend:
            self.braket_backend.validate(self.braket_task_ir)

        super().run_validation()


class QuEraTask(BraketTask):
    quera_backend: Optional[QuEraBackend]
    quera_task_ir: Optional[QuEraTaskSpecification]

    def submit(self):
        if self.quera_backend:
            task_id = self.quera_backend.submit_task(self.quera_task_ir)
            return HardwareTaskFuture(
                task_id=task_id,
                quera_backend=self.quera_backend,
                quera_task_ir=self.quera_task_ir,
                parallel_decoder=self.parallel_decoder,
            )
        return super().submit()

    def run_validation(self) -> None:
        if self.quera_backend:
            self.quera_backend.validate(self.quera_backend)

        super().run_validation()


class HardwareTask(QuEraTask):
    def __init__(self, **kwargs):
        task_ir = kwargs.get("task_ir")
        backend = kwargs.get("backend")
        parallel_decoder = kwargs.get("parallel_decoder")

        match (task_ir, backend):
            case (BraketTaskSpecification(), BraketBackend()):
                super().__init__(
                    braket_task_ir=task_ir,
                    braket_backend=backend,
                    parallel_decoder=parallel_decoder,
                )
            case (QuEraTaskSpecification(), BraketBackend()):
                super().__init__(
                    braket_task_ir=to_braket_task_ir(task_ir),
                    braket_backend=backend,
                    parallel_decoder=parallel_decoder,
                )
            case (QuEraTaskSpecification(), QuEraBackend()):
                super().__init__(
                    quera_task_ir=task_ir,
                    quera_backend=backend,
                    parallel_decoder=parallel_decoder,
                )
            case (QuEraTaskSpecification(), DumbMockBackend()):
                super().__init__(
                    mock_task_ir=task_ir,
                    mock_backend=backend,
                    parallel_decoder=parallel_decoder,
                )
            case _:
                super().__init__(**kwargs)


class MockTaskFuture(BaseModel, TaskFuture):
    task_id: str
    mock_backend: Optional[DumbMockBackend]
    mock_task_ir: Optional[QuEraTaskSpecification]

    def fetch(self) -> QuEraTaskResults:
        if self.mock_backend:
            return self.mock_backend.task_results(self.task_id)

        return super().fetch()

    def status(self) -> QuEraTaskStatusCode:
        if self.mock_backend:
            return self.mock_backend.task_status(self.task_id)

        return super().status()

    def cancel(self) -> None:
        if self.mock_backend:
            return self.mock_backend.cancel_task(self.task_id)

        return super().cancel()


class BraketTaskFuture(MockTaskFuture):
    braket_backend: Optional[BraketBackend]
    to_braket_task_ir: Optional[BraketTaskSpecification]

    def fetch(self) -> QuEraTaskResults:
        if self.braket_backend:
            return self.braket_backend.task_results(self.task_id)

        return super().fetch()

    def status(self) -> QuEraTaskStatusCode:
        if self.braket_backend:
            return self.braket_backend.task_status(self.task_id)

        return super().status()

    def cancel(self) -> None:
        if self.braket_backend:
            return self.braket_backend.cancel_task(self.task_id)

        return super().cancel()


class QuEraTaskFuture(BraketTaskFuture):
    quera_backend: Optional[QuEraBackend]
    quera_task_ir: Optional[QuEraTaskSpecification]

    def fetch(self) -> QuEraTaskResults:
        if self.quera_backend:
            return self.quera_backend.task_results(self.task_id)

        return super().fetch()

    def status(self) -> QuEraTaskStatusCode:
        if self.quera_backend:
            return self.quera_backend.task_status(self.task_id)

        return super().status()

    def cancel(self) -> None:
        if self.quera_backend:
            return self.quera_backend.cancel_task(self.task_id)

        return super().cancel()


class HardwareTaskFuture(QuEraTaskFuture):
    parallel_decoder: Optional[ParallelDecoder]


class HardwareJob(BaseModel, Job):
    tasks: List[HardwareTask] = []
    submit_order: List[int] = []

    def __init__(self, tasks: List[HardwareTask] = [], submit_order=None):
        if submit_order is None:
            submit_order = list(np.random.permutation(len(tasks)))

        super().__init__(tasks=tasks, submit_order=submit_order)

    def submit(self) -> "HardwareFuture":
        try:
            self.tasks[0].run_validation()
            has_validation = True
        except NotImplementedError:
            has_validation = False

        if has_validation:
            for task in self.tasks[1:]:
                task.run_validation()

        # submit tasks in random order but store them
        # in the original order of tasks.
        futures = [None for task in self.tasks]
        for task_index in self.submit_order:
            try:
                futures[task_index] = self.tasks[task_index].submit()
            except BaseException as e:
                for future in futures:
                    if future is not None:
                        future.cancel()
                raise e

        return HardwareFuture(futures=futures)

    def json(self, exclude_none=True, by_alias=True, **json_options) -> str:
        return super().json(
            exclude_none=exclude_none, by_alias=by_alias, **json_options
        )

    def init_from_dict(self, **params) -> None:
        match params:
            case {
                "tasks": list() as tasks_json,
                "submit_order": list() as submit_order,
            }:
                self.tasks = [HardwareTask(**task_json) for task_json in tasks_json]
                self.submit_order = submit_order
            case {
                "tasks": list() as tasks_json,
                "submit_order": list() as submit_order,
                "parallel_decoder": dict() as parallel_decoder,
            }:
                self.tasks = [HardwareTask(**task_json) for task_json in tasks_json]
                self.submit_order = submit_order
                self.parallel_decoder = ParallelDecoder(**parallel_decoder)
            case _:
                raise ValueError(
                    "Cannot parse JSON file to HardwareJob, invalided format."
                )


class HardwareFuture(BaseModel, Future):
    futures: List[HardwareTaskFuture]
    task_results_ir: List[QuEraTaskResults] = []

    def __init__(self, futures: List[HardwareTaskFuture] = []):
        super().__init__(futures=futures)

    def _futures(self):
        return self.futures

    def cancel(self) -> None:
        for future in self.futures:
            future.cancel()

    def fetch(self, cache_results: bool = False) -> List[QuEraTaskResults]:
        if cache_results:
            if self.task_results_ir:
                return self.task_results_ir

            self.task_results_ir = [future.fetch() for future in self.futures]
            return self.task_results_ir
        else:
            return [future.fetch() for future in self.futures]

    def json(self, exclude_none=True, by_alias=True, **json_options) -> str:
        return super().json(
            exclude_none=exclude_none, by_alias=by_alias, **json_options
        )

    def init_from_dict(self, **params) -> None:
        match params:
            case {
                "futures": list() as futures,
                "task_results_ir": list() as task_results_json,
            }:
                self.futures = [
                    HardwareTaskFuture(**future_json) for future_json in futures
                ]
                self.task_results_ir = [
                    QuEraTaskResults(**task_result_json)
                    for task_result_json in task_results_json
                ]
            case {
                "futures": list() as futures,
            }:
                self.tasks = [HardwareTask(**future_json) for future_json in futures]
            case _:
                raise ValueError(
                    "Cannot parse JSON file to HardwareFuture, invalided format."
                )
