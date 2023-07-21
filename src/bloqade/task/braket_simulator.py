from braket.devices import LocalSimulator

from bloqade.submission.ir.braket import (
    BraketTaskSpecification,
    from_braket_task_results,
)
from bloqade.submission.ir.task_results import QuEraTaskResults
from bloqade.task.base import BatchResult, BatchTask, Geometry, Task, TaskShotResults
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

    def submit(self, **kwargs) -> "BraketEmulatorTaskResults":
        aws_task = LocalSimulator("braket_ahs").run(
            self.task_ir.program, shots=self.task_ir.nshots, **kwargs
        )

        return BraketEmulatorTaskResults(
            braket_emulator_task=self,
            task_results_ir=from_braket_task_results(aws_task.result()),
        )


class BraketEmulatorTaskResults(JSONInterface, TaskShotResults[BraketEmulatorTask]):
    braket_emulator_task: BraketEmulatorTask
    task_results_ir: QuEraTaskResults

    def _task(self) -> BraketEmulatorTask:
        return self.braket_emulator_task

    def _quera_task_result(self) -> QuEraTaskResults:
        return self.task_results_ir


class BraketEmulatorBatchResult(JSONInterface, BatchResult[BraketEmulatorTaskResults]):
    braket_emulator_task_results: OrderedDict[int, BraketEmulatorTaskResults]

    def _task_results(self) -> OrderedDict[int, BraketEmulatorTaskResults]:
        return self.braket_emulator_task_results


class BraketEmulatorBatchTask(JSONInterface, BatchTask[BraketEmulatorTask]):
    braket_emulator_tasks: OrderedDict[int, BraketEmulatorTask] = {}

    def _tasks(self) -> OrderedDict[int, BraketEmulatorTask]:
        return self.braket_emulator_tasks

    def submit(
        self,
        multiprocessing: bool = False,
        max_workers: Optional[int] = None,
        progress_bar: bool = False,
        **kwargs,
    ) -> BraketEmulatorBatchResult:
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
