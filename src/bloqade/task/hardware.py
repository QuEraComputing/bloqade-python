from bloqade.submission.ir.task_results import QuEraTaskResults
from bloqade.submission.mock import DumbMockBackend
from bloqade.submission.quera import QuEraBackend
from bloqade.submission.braket import BraketBackend
from bloqade.submission.ir.task_specification import (
    QuEraTaskSpecification,
)
from bloqade.submission.ir.parallel import ParallelDecoder
from bloqade.submission.ir.task_results import QuEraTaskStatusCode
from bloqade.task.base import (
    Geometry,
    SerializableTask,
    SerializableTaskFuture,
    SerializableBatchTask,
    SerializableBatchFuture,
)

from collections import OrderedDict
from typing import Optional, Type, Union


class MockTask(SerializableTask):
    task_ir: Optional[QuEraTaskSpecification]
    mock_backend: Optional[DumbMockBackend]
    parallel_decoder: Optional[ParallelDecoder]

    def _geometry(self) -> Geometry:
        return Geometry(
            sites=self.task_ir.lattice.sites,
            filling=self.task_ir.lattice.filling,
            parallel_decoder=self.parallel_decoder,
        )

    def _backend(self):
        if self.mock_backend:
            return self.mock_backend

        return super()._backend()

    def submit(self):
        if self.mock_backend:
            task_id = self.mock_backend.submit_task(self.task_ir)
            return HardwareTaskFuture(
                task_id=task_id,
                hardware_task=self,
            )
        return super().submit()

    def run_validation(self) -> None:
        if self.mock_backend:
            return self.mock_backend.validate_task(self.task_ir)

        return super().run_validation()


class BraketTask(MockTask):
    braket_backend: Optional[BraketBackend]

    def _backend(self):
        if self.braket_backend:
            return self.braket_backend

        return super()._backend()

    def submit(self):
        if self.braket_backend:
            task_id = self.braket_backend.submit_task(self.task_ir)
            return HardwareTaskFuture(
                task_id=task_id,
                hardware_task=self,
            )
        return super().submit()

    def run_validation(self) -> None:
        if self.braket_backend:
            return self.braket_backend.validate_task(self.task_ir)

        return super().run_validation()


class QuEraTask(BraketTask):
    quera_backend: Optional[QuEraBackend]

    def _backend(self):
        if self.quera_backend:
            return self.quera_backend

        return super()._backend()

    def submit(self):
        if self.quera_backend:
            task_id = self.quera_backend.submit_task(self.task_ir)
            return HardwareTaskFuture(
                task_id=task_id,
                hardware_task=self,
            )
        return super().submit()

    def run_validation(self) -> None:
        if self.quera_backend:
            return self.quera_backend.validate_task(self.task_ir)

        return super().run_validation()


class HardwareTask(QuEraTask):
    def __init__(
        self,
        task_ir: QuEraTaskSpecification,
        backend: Optional[Union[QuEraBackend, BraketBackend, DumbMockBackend]] = None,
        parallel_decoder: Optional[ParallelDecoder] = None,
        **kwargs,
    ):
        match backend:
            case BraketBackend():
                super().__init__(
                    task_ir=task_ir,
                    braket_backend=backend,
                    parallel_decoder=parallel_decoder,
                )
            case QuEraBackend():
                super().__init__(
                    task_ir=task_ir,
                    quera_backend=backend,
                    parallel_decoder=parallel_decoder,
                )
            case DumbMockBackend():
                super().__init__(
                    task_ir=task_ir,
                    mock_backend=backend,
                    parallel_decoder=parallel_decoder,
                )
            case _:
                super().__init__(
                    task_ir=task_ir, parallel_decoder=parallel_decoder, **kwargs
                )


class HardwareTaskFuture(SerializableTaskFuture):
    hardware_task: Optional[HardwareTask]
    task_id: Optional[str]
    task_result_ir: Optional[QuEraTaskResults]

    def __init__(self, **kwargs):
        if "task" in kwargs.keys():
            kwargs["hardware_task"] = kwargs["task"]
            kwargs.pop("task")

        super().__init__(**kwargs)

    def _task(self) -> HardwareTask:
        return self.hardware_task

    def fetch(self, cache_result=False) -> QuEraTaskResults:
        if self.task_id is None:
            raise ValueError("Task ID not found.")

        if self.task_result_ir:
            return self.task_result_ir

        task_result_ir = self.hardware_task.backend.task_results(self.task_id)

        if cache_result:
            self.task_result_ir = task_result_ir

        return task_result_ir

    def status(self) -> QuEraTaskStatusCode:
        if self.task_id is None:
            raise ValueError("Task ID not found.")

        return self.hardware_task.backend.task_status(self.task_id)

    def cancel(self) -> None:
        if self.task_id is None:
            raise ValueError("Task ID not found.")

        return self.hardware_task.backend.cancel_task(self.task_id)

    def _resubmit_if_not_submitted(self) -> "HardwareTaskFuture":
        if self.task_id:
            return self
        else:
            return self.hardware_task.submit()


class HardwareBatchTask(SerializableBatchTask):
    hardware_tasks: OrderedDict[int, HardwareTask] = OrderedDict()

    def _task_future_class(self) -> Type[HardwareTaskFuture]:
        return HardwareTaskFuture

    def _tasks(self) -> OrderedDict[int, HardwareTask]:
        return self.hardware_tasks

    def _emit_batch_future(
        self, futures: OrderedDict[int, HardwareTaskFuture]
    ) -> "HardwareBatchFuture":
        return HardwareBatchFuture(hardware_task_futures=futures)

    def _init_from_dict(self, **params) -> None:
        match params:
            case {"hardware_tasks": dict() as tasks}:
                self.hardware_tasks = OrderedDict(
                    [
                        (int(task_number), HardwareTask(**tasks[task_number]))
                        for task_number in tasks.keys()
                    ]
                )
            case _:
                raise ValueError(
                    f"Cannot parse JSON file to {self.__class__.__name__}, "
                    "invalided format."
                )


class HardwareBatchFuture(SerializableBatchFuture):
    hardware_task_futures: OrderedDict[int, HardwareTaskFuture] = OrderedDict()

    def _task_futures(self) -> OrderedDict[int, HardwareTaskFuture]:
        return self.hardware_task_futures

    def _init_from_dict(self, **params) -> None:
        match params:
            case {"hardware_task_futures": dict() as futures}:
                self.hardware_task_futures = OrderedDict(
                    [
                        (int(task_number), HardwareTaskFuture(**futures[task_number]))
                        for task_number in futures.keys()
                    ]
                )
            case _:
                raise ValueError(
                    f"Cannot parse JSON file to {self.__class__.__name__}, "
                    "invalided format."
                )
