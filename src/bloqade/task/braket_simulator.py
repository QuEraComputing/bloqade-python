from pydantic import BaseModel
from braket.devices import LocalSimulator

from bloqade.submission.ir.braket import (
    BraketTaskSpecification,
    from_braket_task_results,
)
from bloqade.submission.ir.task_results import (
    QuEraTaskResults,
    QuEraTaskStatusCode,
)
from bloqade.task.base import (
    Future,
    Geometry,
    JSONInterface,
    Task,
    TaskFuture,
    Job,
)
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor


class BraketEmulatorTask(BaseModel, Task):
    task_ir: BraketTaskSpecification

    def submit(self) -> "BraketEmulatorTaskFuture":
        aws_task = LocalSimulator("braket_ahs").run(
            self.task_ir.program, shots=self.task_ir.nshots
        )

        return BraketEmulatorTaskFuture(
            task_ir=self.task_ir,
            task_results_ir=from_braket_task_results(aws_task.result()),
        )


class BraketEmulatorTaskFuture(BaseModel, TaskFuture):
    task_ir: BraketTaskSpecification
    task_results_ir: QuEraTaskResults

    def _task_geometry(self) -> Geometry:
        return Geometry(
            sites=self.task_ir.program.setup.ahs_register.sites,
            filling=self.task_ir.program.setup.ahs_register.filling,
            parallel_decoder=None,
        )

    def fetch(self, cache_result=False) -> QuEraTaskResults:
        return self.task_results_ir

    def status(self) -> QuEraTaskStatusCode:
        return QuEraTaskStatusCode.Completed

    def cancel(self) -> None:
        pass


class BraketEmulatorJob(JSONInterface, Job):
    tasks: List[BraketEmulatorTask]

    def _task_list(self) -> List[BraketEmulatorTask]:
        return self.tasks

    def _emit_future(
        self, futures: List[BraketEmulatorTaskFuture]
    ) -> "BraketEmulatorFuture":
        return BraketEmulatorFuture(futures=futures)

    def submit(
        self,
        submission_order: Optional[List[int]] = None,
        max_workers: Optional[int] = None,
    ) -> Future:
        if submission_order is None:
            submission_order = list(range(len(self.tasks)))

        futures = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for i in submission_order:
                futures.append(executor.submit(self.tasks[i].submit))

        return self._emit_future([future.result() for future in futures])


class BraketEmulatorFuture(JSONInterface, Future):
    futures: List[BraketEmulatorTaskFuture]

    def futures_list(self) -> List[BraketEmulatorTaskFuture]:
        return self.futures
