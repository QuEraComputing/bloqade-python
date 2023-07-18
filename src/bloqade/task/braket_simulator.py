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
    SerializableBatchFuture,
    SerializableBatchTask,
    SerializableTask,
    SerializableTaskFuture,
    Geometry,
    Task,
)
from typing import Optional, Type
from concurrent.futures import ProcessPoolExecutor
from collections import OrderedDict


class BraketEmulatorTask(SerializableTask):
    task_ir: BraketTaskSpecification

    def _geometry(self) -> Geometry:
        return Geometry(
            sites=self.task_ir.lattice.sites,
            filling=self.task_ir.lattice.filling,
        )

    def submit(self, **kwargs) -> "BraketEmulatorTaskFuture":
        aws_task = LocalSimulator("braket_ahs").run(
            self.task_ir.program, shots=self.task_ir.nshots, **kwargs
        )

        return BraketEmulatorTaskFuture(
            braket_emulator_task=self,
            task_results_ir=from_braket_task_results(aws_task.result()),
        )


class BraketEmulatorTaskFuture(SerializableTaskFuture):
    braket_emulator_task: BraketEmulatorTask
    task_results_ir: QuEraTaskResults

    def _task(self) -> Task:
        return self.braket_emulator_task

    def _resubmit_if_not_submitted(self) -> "BraketEmulatorTaskFuture":
        return self

    def _init_from_dict(self, **params) -> None:
        match params:
            case {
                "task_results_ir": dict() as task_results_ir,
                "braket_emulator_task": dict() as braket_emulator_task,
            }:
                self.task_results_ir = QuEraTaskResults(**task_results_ir)
                self.braket_emulator_task = BraketEmulatorTask(**braket_emulator_task)
            case _:
                raise ValueError(
                    f"Cannot parse JSON file to {self.__class__.__name__}, "
                    "invalided format."
                )

    def fetch(self, cache_result=False) -> QuEraTaskResults:
        return self.task_results_ir

    def status(self) -> QuEraTaskStatusCode:
        return QuEraTaskStatusCode.Completed

    def cancel(self) -> None:
        pass


class BraketEmulatorBatchTask(SerializableBatchTask):
    braket_emulator_tasks: OrderedDict[int, BraketEmulatorTask] = {}

    def _task_future_class(self) -> Type[BraketEmulatorTaskFuture]:
        return BraketEmulatorTaskFuture

    def _tasks(self) -> OrderedDict[int, BraketEmulatorTask]:
        return self.braket_emulator_tasks

    def _emit_batch_future(
        self, futures: OrderedDict[int, BraketEmulatorTaskFuture]
    ) -> "BraketEmulatorBatchFuture":
        return BraketEmulatorBatchFuture(braket_emulator_task_futures=futures)

    def _init_from_dict(self, **params) -> None:
        match params:
            case {"braket_emulator_tasks": dict() as tasks}:
                self.braket_emulator_tasks = OrderedDict(
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
    ) -> "BraketEmulatorBatchFuture":
        if multiprocessing:
            futures = {}
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                for task_number, task in self.braket_emulator_tasks.items():
                    futures[task_number] = executor.submit(task.submit, **kwargs)

            return self._emit_batch_future(
                {
                    task_number: future.result()
                    for task_number, future in futures.items()
                }
            )
        else:
            return super().submit()


class BraketEmulatorBatchFuture(SerializableBatchFuture):
    braket_emulator_task_futures: OrderedDict[int, BraketEmulatorTaskFuture]

    def _task_futures(self) -> OrderedDict[int, BraketEmulatorTaskFuture]:
        return self.braket_emulator_task_futures

    def _init_from_dict(self, **params) -> None:
        match params:
            case {"braket_emulator_task_futures": dict() as futures}:
                self.braket_emulator_task_futures = OrderedDict(
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
