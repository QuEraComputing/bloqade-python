from braket.devices import LocalSimulator

from bloqade.submission.ir.braket import (
    BraketTaskSpecification,
    from_braket_task_results,
)
from bloqade.submission.ir.task_results import QuEraTaskResults
from bloqade.task.base import BatchResult, BatchTask, Geometry, Task, TaskShotResult
from bloqade.task.cloud_base import JSONInterface
from typing import Optional
from concurrent.futures import ProcessPoolExecutor
from collections import OrderedDict
import tqdm


class BraketEmulatorTask(JSONInterface, Task):
    task_ir: BraketTaskSpecification

    def _geometry(self) -> Geometry:
        return Geometry(
            sites=self.task_ir.lattice.sites,
            filling=self.task_ir.lattice.filling,
        )

    def submit(self, **kwargs) -> "BraketEmulatorTaskResult":
        aws_task = LocalSimulator("braket_ahs").run(
            self.task_ir.program, shots=self.task_ir.nshots, **kwargs
        )

        return BraketEmulatorTaskResult(
            braket_emulator_task=self,
            task_results_ir=from_braket_task_results(aws_task.result()),
        )


class BraketEmulatorTaskResult(JSONInterface, TaskShotResult):
    braket_emulator_task: BraketEmulatorTask
    task_results_ir: QuEraTaskResults

    def _task(self) -> Task:
        return self.braket_emulator_task

    def _quera_task_result(self) -> QuEraTaskResults:
        return self.task_results_ir


class BraketEmulatorBatchTask(JSONInterface, BatchTask):
    braket_emulator_tasks: OrderedDict[int, BraketEmulatorTask] = {}

    def _tasks(self) -> OrderedDict[int, BraketEmulatorTask]:
        return self.braket_emulator_tasks

    def submit(
        self,
        multiprocessing: bool = False,
        max_workers: Optional[int] = None,
        progress_bar: bool = False,
        **kwargs,
    ) -> "BraketEmulatorBatchResult":
        if multiprocessing:
            futures = OrderedDict()
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                for task_number, task in self.tasks.items():
                    futures[task_number] = executor.submit(task.submit, **kwargs)

            if progress_bar:
                iterator = tqdm.tqdm(futures.items())
            else:
                iterator = futures.items()

            task_results = OrderedDict()
            for task_number, future in iterator:
                task_results[task_number] = future.result()

        else:
            if progress_bar:
                iterator = tqdm.tqdm(self.tasks.items())
            else:
                iterator = self.tasks.items()

            task_results = OrderedDict()
            for task_number, task in iterator:
                task_results[task_number] = task.submit(**kwargs)

        return BraketEmulatorBatchResult(braket_emulator_task_results=task_results)


class BraketEmulatorBatchResult(JSONInterface, BatchResult):
    braket_emulator_task_results: OrderedDict[int, BraketEmulatorTaskResult]

    def __init__(self, **kwargs):
        if "futures" in kwargs:
            kwargs["braket_emulator_task_futures"] = kwargs.pop("futures")

        super().__init__(**kwargs)

    def _task_results(self) -> OrderedDict[int, BraketEmulatorTaskResult]:
        return self.braket_emulator_task_results
