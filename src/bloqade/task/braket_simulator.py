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
from typing import Optional
from concurrent.futures import ProcessPoolExecutor
from collections import OrderedDict


class BraketEmulatorTask(BaseModel, Task):
    task_ir: BraketTaskSpecification

    def submit(self, **kwargs) -> "BraketEmulatorTaskFuture":
        aws_task = LocalSimulator("braket_ahs").run(
            self.task_ir.program, shots=self.task_ir.nshots, **kwargs
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
    tasks: OrderedDict[int, BraketEmulatorTask] = {}

    def _task_dict(self) -> OrderedDict[int, BraketEmulatorTask]:
        return self.tasks

    def _emit_future(
        self, futures: OrderedDict[int, BraketEmulatorTaskFuture]
    ) -> "BraketEmulatorFuture":
        return BraketEmulatorFuture(futures=futures)

    def init_from_dict(self, **params) -> None:
        match params:
            case {"tasks": dict() as tasks}:
                self.tasks = OrderedDict(
                    [
                        (task_number, BraketEmulatorTask(**tasks[task_number]))
                        for task_number in sorted(tasks.keys())
                    ]
                )
            case _:
                raise ValueError(
                    f"Cannot parse JSON file to {self.__class__.__name__}, "
                    "invalided format."
                )

    def submit(
        self, multiprocessing: bool = False, max_workers: Optional[int] = None, **kwargs
    ) -> Future:
        if multiprocessing:
            futures = {}
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                for task_number, task in self.tasks.items():
                    futures[task_number] = executor.submit(task.submit, **kwargs)

            return self._emit_future(
                {
                    task_number: future.result()
                    for task_number, future in futures.items()
                }
            )
        else:
            return super().submit()


class BraketEmulatorFuture(JSONInterface, Future):
    futures: OrderedDict[int, BraketEmulatorTaskFuture]

    def futures_dict(self) -> OrderedDict[int, BraketEmulatorTaskFuture]:
        return self.futures

    def init_from_dict(self, **params) -> None:
        match params:
            case {"futures": dict() as futures}:
                self.futures = OrderedDict(
                    [
                        (task_number, BraketEmulatorTaskFuture(**futures[task_number]))
                        for task_number in sorted(futures.keys())
                    ]
                )
            case _:
                raise ValueError(
                    f"Cannot parse JSON file to {self.__class__.__name__}, "
                    "invalided format."
                )
