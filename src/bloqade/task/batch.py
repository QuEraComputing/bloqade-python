from pydantic import BaseModel
from typing import List

from .hardware import HardwareTask, HardwareTaskFuture


class HardwareBatch(BaseModel):
    tasks: List[HardwareTask]

    def submit(self):
        try:
            self.tasks[0].validate()
            has_validation = True
        except NotImplementedError:
            has_validation = False

        futures = []
        if has_validation:
            for task in self.tasks[1:]:
                task.validate()

        for task in self.tasks:
            try:
                future = task.submit()
                futures.append(future)
            except BaseException as e:
                for future in futures:
                    future.cancel()
                raise e

        return HardwareBatchFuture(futures=futures)


class HardwareBatchFuture(BaseModel):
    futures: List[HardwareTaskFuture]

    def cancel(self):
        for future in self.futures:
            future.cancel()

    def fetch(self):
        for future in self.futures:
            future.fetch()
