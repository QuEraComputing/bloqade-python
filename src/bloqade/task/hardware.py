import warnings
from bloqade.submission.base import ValidationError
from bloqade.submission.mock import DumbMockBackend
from bloqade.submission.quera import QuEraBackend
from bloqade.submission.braket import BraketBackend
from bloqade.submission.ir.task_specification import (
    QuEraTaskSpecification,
)
from bloqade.submission.ir.task_results import QuEraTaskResults
from bloqade.submission.ir.parallel import ParallelDecoder
from bloqade.submission.ir.task_results import QuEraTaskStatusCode
from bloqade.task.base import Geometry
from bloqade.task.cloud_base import (
    CloudBatchTask,
    CloudBatchResult,
    CloudTask,
    CloudTaskResults,
)
from collections import OrderedDict
from typing import Optional, Union


class MockTask(CloudTask):
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


class BraketTask(MockTask):
    braket_backend: Optional[BraketBackend]

    def _backend(self):
        if self.braket_backend:
            return self.braket_backend

        return super()._backend()


class QuEraTask(BraketTask):
    quera_backend: Optional[QuEraBackend]

    def _backend(self):
        if self.quera_backend:
            return self.quera_backend

        return super()._backend()


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

    def submit(self) -> "HardwareTaskShotResults":
        task_id = self.backend.submit_task(self.task_ir)
        return HardwareTaskShotResults(
            task_id=task_id,
            hardware_task=self,
        )

    def run_validation(self) -> str:
        try:
            self.backend.validate_task(self.task_ir)
        except ValidationError as e:
            return str(e)

    def future_no_task_id(self) -> "HardwareTaskShotResults":
        return HardwareTaskShotResults(hardware_task=self)


class HardwareTaskShotResults(CloudTaskResults[HardwareTask]):
    hardware_task: Optional[HardwareTask]
    task_result_ir: Optional[QuEraTaskResults]

    def _task(self):
        return self.hardware_task

    def fetch_task_result(self, cache_result=False) -> QuEraTaskResults:
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
            warnings.warn("Cannot cancel task, missing task id.")
            return

        self.hardware_task.backend.cancel_task(self.task_id)


class HardwareBatchResult(CloudBatchResult[HardwareTaskShotResults]):
    hardware_task_shot_results: OrderedDict[
        int, HardwareTaskShotResults
    ] = OrderedDict()

    def _task_results(self) -> OrderedDict[int, HardwareTaskShotResults]:
        return self.hardware_task_shot_results


class HardwareBatchTask(CloudBatchTask[HardwareTask, HardwareBatchResult]):
    hardware_tasks: OrderedDict[int, HardwareTask] = OrderedDict()

    def _tasks(self):
        return self.hardware_tasks

    def _emit_batch_future(
        self, task_results: OrderedDict[int, HardwareTaskShotResults]
    ) -> "HardwareBatchResult":
        return HardwareBatchResult(hardware_task_shot_results=task_results)
