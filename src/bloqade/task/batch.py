from pydantic import BaseModel
from typing import List

from .hardware import HardwareTask, HardwareTaskFuture
from bloqade.submission.quera_api_client.ir.task_results import QuEraTaskResults

import numpy as np


class HardwareBatch(BaseModel):
    tasks: List[HardwareTask]
    task_submit_order: List[int]

    def __init__(self, tasks: List[HardwareTask], task_submit_order=None):
        if task_submit_order is None:
            task_submit_order = list(np.random.permutation(len(tasks)))

        super().__init__(tasks=tasks, task_submit_order=task_submit_order)

    def submit(self):
        try:
            self.tasks[0].validate()
            has_validation = True
        except NotImplementedError:
            has_validation = False

        if has_validation:
            for task in self.tasks[1:]:
                task.validate()

        # submit tasks in random order but store them
        # in the original order of tasks.
        futures = [None for task in self.tasks]
        for task_index in self.task_submit_order:
            try:
                futures[task_index] = self.tasks[task_index].submit()
            except BaseException as e:
                for future in futures:
                    if future is not None:
                        future.cancel()
                raise e

        return HardwareBatchFuture(futures=futures)


class HardwareBatchFuture(BaseModel):
    futures: List[HardwareTaskFuture]
    task_result_ir_list: List[QuEraTaskResults] = []

    def cancel(self):
        for future in self.futures:
            future.cancel()

    def fetch(self):
        task_result_ir_list = []
        for future in self.futures:
            task_result_ir_list.append(future.fetch())

        return task_result_ir_list

    @property
    def task_result_ir_list(self):
        if self.task_result_ir_list:
            return self.task_result_ir_list

        self.task_result_ir_list = self.fetch()

        return self.task_result_ir_list
