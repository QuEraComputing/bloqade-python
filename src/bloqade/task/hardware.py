from pydantic import BaseModel
from bloqade.submission.ir.task_results import QuEraTaskResults
from bloqade.submission.mock import DumbMockBackend
from bloqade.submission.quera import QuEraBackend
from bloqade.submission.braket import BraketBackend
from bloqade.submission.ir.task_specification import (
    QuEraTaskSpecification,
)
from bloqade.submission.ir.parallel import ParallelDecoder
from bloqade.submission.ir.task_results import QuEraTaskStatusCode
from bloqade.task.base import Task, Future, Geometry, TaskFuture, Job, JSONInterface


from typing import Optional, List, Union


class MockTask(BaseModel, Task):
    task_ir: Optional[QuEraTaskSpecification]
    mock_backend: Optional[DumbMockBackend]
    parallel_decoder: Optional[ParallelDecoder]

    def submit(self):
        if self.mock_backend:
            task_id = self.mock_backend.submit_task(self.task_ir)
            return HardwareTaskFuture(
                task_id=task_id,
                task_ir=self.task_ir,
                mock_backend=self.mock_backend,
                parallel_decoder=self.parallel_decoder,
            )
        return super().submit()

    def run_validation(self) -> None:
        if self.mock_backend:
            self.mock_backend.validate_task(self.task_ir)

        super().run_validation()


class BraketTask(MockTask):
    braket_backend: Optional[BraketBackend]

    def submit(self):
        if self.braket_backend:
            task_id = self.braket_backend.submit_task(self.task_ir)
            return HardwareTaskFuture(
                task_id=task_id,
                task_ir=self.task_ir,
                braket_backend=self.braket_backend,
                parallel_decoder=self.parallel_decoder,
            )
        return super().submit()

    def run_validation(self) -> None:
        if self.braket_backend:
            self.braket_backend.validate_task(self.task_ir)

        super().run_validation()


class QuEraTask(BraketTask):
    quera_backend: Optional[QuEraBackend]

    def submit(self):
        if self.quera_backend:
            task_id = self.quera_backend.submit_task(self.task_ir)
            return HardwareTaskFuture(
                task_id=task_id,
                task_ir=self.task_ir,
                quera_backend=self.quera_backend,
                parallel_decoder=self.parallel_decoder,
            )
        return super().submit()

    def run_validation(self) -> None:
        if self.quera_backend:
            self.quera_backend.validate_task(self.task_ir)

        super().run_validation()


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


class MockTaskFuture(BaseModel, TaskFuture):
    task_id: str
    task_ir: Optional[QuEraTaskSpecification]
    task_result_ir: Optional[QuEraTaskResults]
    mock_backend: Optional[DumbMockBackend]
    parallel_decoder: Optional[ParallelDecoder]

    def _task_geometry(self) -> Geometry:
        if self.parallel_decoder:
            cluster_indices = self.parallel_decoder.get_cluster_indices()
            cluster_index = cluster_indices[(0, 0)]
            sites = [self.task_ir.lattice.sites[index] for index in cluster_index]
            filling = [self.task_ir.lattice.filling[index] for index in cluster_index]
            return Geometry(
                sites=sites, filling=filling, parallel_decoder=self.parallel_decoder
            )
        else:
            return Geometry(
                sites=self.task_ir.lattice.sites,
                filling=self.task_ir.lattice.filling,
                parallel_decoder=self.parallel_decoder,
            )

    def fetch(self, cache_result: bool = False) -> QuEraTaskResults:
        if self.mock_backend:
            if self.task_result_ir:
                return self.task_result_ir

            if cache_result:
                self.task_result_ir = self.mock_backend.task_results(self.task_id)
                return self.task_result_ir
            else:
                return self.mock_backend.task_results(self.task_id)

        return super().fetch(cache_result=cache_result)

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

    def fetch(self, cache_result: bool = False) -> QuEraTaskResults:
        if self.braket_backend:
            if self.task_result_ir:
                return self.task_result_ir

            if cache_result:
                self.task_result_ir = self.braket_backend.task_results(self.task_id)
                return self.task_result_ir
            else:
                return self.braket_backend.task_results(self.task_id)

        return super().fetch(cache_result=cache_result)

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

    def fetch(self, cache_result: bool = False) -> QuEraTaskResults:
        if self.quera_backend:
            if self.task_result_ir:
                return self.task_result_ir

            if cache_result:
                self.task_result_ir = self.quera_backend.task_results(self.task_id)
                return self.task_result_ir
            else:
                return self.quera_backend.task_results(self.task_id)

        return super().fetch(cache_result=cache_result)

    def status(self) -> QuEraTaskStatusCode:
        if self.quera_backend:
            return self.quera_backend.task_status(self.task_id)

        return super().status()

    def cancel(self) -> None:
        if self.quera_backend:
            return self.quera_backend.cancel_task(self.task_id)

        return super().cancel()


class HardwareTaskFuture(QuEraTaskFuture):
    pass


class HardwareJob(JSONInterface, Job):
    tasks: List[HardwareTask] = []

    def _task_list(self) -> List[HardwareTask]:
        return self.tasks

    def _emit_future(self, futures: List[HardwareTaskFuture]) -> "HardwareFuture":
        return HardwareFuture(futures=futures)

    def init_from_dict(self, **params) -> None:
        match params:
            case {"tasks": list() as tasks_json}:
                self.tasks = [HardwareTask(**task_json) for task_json in tasks_json]
            case _:
                raise ValueError(
                    f"Cannot parse JSON file to {self.__class__.__name__}, "
                    "invalided format."
                )


class HardwareFuture(JSONInterface, Future):
    futures: List[HardwareTaskFuture] = []

    def futures_list(self) -> List[HardwareTaskFuture]:
        return self.futures

    def init_from_dict(self, **params) -> None:
        match params:
            case {"futures": list() as futures}:
                self.futures = [
                    HardwareTaskFuture(**future_json) for future_json in futures
                ]
            case _:
                raise ValueError(
                    f"Cannot parse JSON file to {self.__class__.__name__}, "
                    "invalided format."
                )
