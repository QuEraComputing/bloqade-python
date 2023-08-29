from collections import OrderedDict
from itertools import product
import json
from typing import Union, Optional, List
from .base import Report
from .quera import QuEraTask
from .braket import BraketTask
from .braket_simulator import BraketEmulatorTask
import traceback
import datetime
import sys
import os
import warnings
from bloqade.submission.ir.task_results import (
    QuEraShotStatusCode,
    QuEraTaskStatusCode,
    QuEraTaskResults,
)
import pandas as pd
import numpy as np
from dataclasses import dataclass
from bloqade.submission.base import ValidationError


class Serializable:
    def json(self, **options) -> str:
        from .json import BatchSerializer

        return json.dumps(self, cls=BatchSerializer, **options)


@dataclass
class LocalBatch(Serializable):
    tasks: OrderedDict[int, BraketEmulatorTask]
    name: Optional[str] = None

    def report(self) -> Report:
        ## this potentially can be specialize/disatch
        ## offline
        index = []
        data = []
        metas = []
        geos = []

        for task_number, task in self.tasks.items():
            geometry = task.geometry
            perfect_sorting = "".join(map(str, geometry.filling))
            parallel_decoder = geometry.parallel_decoder

            if parallel_decoder:
                cluster_indices = parallel_decoder.get_cluster_indices()
            else:
                cluster_indices = {(0, 0): list(range(len(perfect_sorting)))}

            shot_iter = filter(
                lambda shot: shot.shot_status == QuEraShotStatusCode.Completed,
                task.result().shot_outputs,
            )

            for shot, (cluster_coordinate, cluster_index) in product(
                shot_iter, cluster_indices.items()
            ):
                pre_sequence = "".join(
                    map(
                        str,
                        (shot.pre_sequence[index] for index in cluster_index),
                    )
                )

                post_sequence = np.asarray(
                    [shot.post_sequence[index] for index in cluster_index],
                    dtype=np.int8,
                )

                pfc_sorting = "".join(
                    [perfect_sorting[index] for index in cluster_index]
                )

                key = (
                    task_number,
                    cluster_coordinate,
                    pfc_sorting,
                    pre_sequence,
                )

                index.append(key)
                data.append(post_sequence)
            metas.append(task.task_data.metadata)
            geos.append(task.geometry)

        index = pd.MultiIndex.from_tuples(
            index, names=["task_number", "cluster", "perfect_sorting", "pre_sequence"]
        )

        df = pd.DataFrame(data, index=index)
        df.sort_index(axis="index")

        rept = None
        if self.name is None:
            rept = Report(df, metas, geos, "Local")
        else:
            rept = Report(df, metas, geos, self.name)

        return rept

    def rerun(
        self, multiprocessing: bool = False, num_workers: Optional[int] = None, **kwargs
    ):
        return self._run(
            multiprocessing=multiprocessing, num_workers=num_workers, **kwargs
        )

    def _run(
        self, multiprocessing: bool = False, num_workers: Optional[int] = None, **kwargs
    ):
        if multiprocessing:
            from multiprocessing import Pool

            if num_workers is None:
                num_workers = os.cpu_count()

            with Pool(num_workers) as pool:
                async_results = []
                for taks_number, task in self.tasks.items():
                    async_results.append(
                        (taks_number, pool.apply_async(task.run, kwds=kwargs))
                    )

                for taks_number, async_result in async_results:
                    async_result.wait()
                    if async_result.successful():
                        self.tasks[taks_number] = async_result.get()

        else:
            if num_workers is not None:
                raise ValueError(
                    "num_workers is only used when multiprocessing is enabled."
                )
            for task in self.tasks.values():
                task.run(**kwargs)

        return self


# this class get collection of tasks
# basically behaves as a psudo queuing system
# the user only need to store this objecet
@dataclass
class RemoteBatch(Serializable):
    tasks: OrderedDict[int, Union[QuEraTask, BraketTask]]
    name: Optional[str] = None

    class SubmissionException(Exception):
        pass

    @property
    def total_nshots(self):
        nshots = 0
        for task in self.tasks.values():
            nshots += task.task_data.task_ir.nshots
        return nshots

    def cancel(self):
        # cancel all jobs
        for task in self.tasks.values():
            task.cancel()

        return self

    def fetch(self):
        # online, non-blocking
        # pull the results only when its ready
        for task in self.tasks.values():
            task.fetch()

        return self

    def pull(self) -> None:
        # online, blocking
        # pull the results. if its not ready, hanging
        for task in self.tasks.values():
            task.pull()

        return self

    def __repr__(self):
        return str(self.tasks_metric())

    def tasks_metric(self):
        # [TODO] more info on current status
        # offline, non-blocking
        tid = []
        data = []
        for int, task in self.tasks.items():
            tid.append(int)

            dat = [None, None, None]
            dat[0] = task.task_id
            if task.task_id is not None:
                if task.task_result_ir is not None:
                    dat[1] = task.result().task_status.name
                    dat[2] = task.task_data.task_ir.nshots
            data.append(dat)

        return pd.DataFrame(data, index=tid, columns=["task ID", "status", "shots"])

    def remove_invalid_tasks(self):
        warnings.warn("Deprecating", DeprecationWarning)

        # offline, non-blocking
        new_tasks = OrderedDict()
        for task_number, task in self.tasks.items():
            try:
                task.validate()
                # if task.task_result_ir is not None:
                #    if task.task_result_ir.task_status
                #       == QuEraTaskStatusCode.Unaccepted:
                #        raise ValidationError

                new_tasks[task_number] = task
            except ValidationError:
                continue

        return RemoteBatch(new_tasks, name=self.name)

    def resubmit(self, shuffle_submit_order: bool = True):
        # online, non-blocking
        self._submit(shuffle_submit_order, force=True)
        return self

    def _submit(
        self, shuffle_submit_order: bool = True, ignore_submission_error=False, **kwargs
    ):
        # online, non-blocking
        if shuffle_submit_order:
            submission_order = np.random.permutation(list(self.tasks.keys()))
        else:
            submission_order = list(self.tasks.keys())

        for task in self.tasks.values():
            try:
                task.validate()
            except NotImplementedError:
                break

        # submit tasks in random order but store them
        # in the original order of tasks.
        # futures = OrderedDict()
        errors = OrderedDict()
        shuffled_tasks = OrderedDict()
        for task_index in submission_order:
            task = self.tasks[task_index]
            shuffled_tasks[task_index] = task
            try:
                task.submit(**kwargs)
            except BaseException as error:
                # record the error in the error dict
                errors[int(task_index)] = {
                    "exception_type": error.__class__.__name__,
                    "stack trace": traceback.format_exc(),
                }
                task.task_result_ir = QuEraTaskResults(
                    task_status=QuEraTaskStatusCode.Unaccepted
                )

        self.tasks = shuffled_tasks  # permute order using dump way

        if errors:
            time_stamp = datetime.datetime.now()

            if "win" in sys.platform:
                time_stamp = str(time_stamp).replace(":", "~")

            if self.name:
                future_file = f"{self.name}-partial-batch-future-{time_stamp}.json"
                error_file = f"{self.name}-partial-batch-errors-{time_stamp}.json"
            else:
                future_file = f"partial-batch-future-{time_stamp}.json"
                error_file = f"partial-batch-errors-{time_stamp}.json"

            cwd = os.get_cwd()
            # cloud_batch_result.save_json(future_file, indent=2)
            # saving ?

            with open(error_file, "w") as f:
                json.dump(errors, f, indent=2)

            if ignore_submission_error:
                warnings.warn(
                    "One or more error(s) occured during submission, please see "
                    "the following files for more information:\n"
                    f"  - {os.path.join(cwd, future_file)}\n"
                    f"  - {os.path.join(cwd, error_file)}\n",
                    RuntimeWarning,
                )
            else:
                raise RemoteBatch.SubmissionException(
                    "One or more error(s) occured during submission, please see "
                    "the following files for more information:\n"
                    f"  - {os.path.join(cwd, future_file)}\n"
                    f"  - {os.path.join(cwd, error_file)}\n"
                )

        else:
            # TODO: think about if we should automatically save successful submissions
            #       as well.
            pass

    def get_tasks(self, status_codes: List[QuEraTaskStatusCode]) -> "RemoteBatch":
        # offline:
        new_task_results = OrderedDict()
        for task_number, task in self.tasks.items():
            if (task.task_id is not None) and (task._result_exists()):
                if task.task_result_ir.task_status in status_codes:
                    new_task_results[task_number] = task

        return RemoteBatch(new_task_results, name=self.name)

    def remove_tasks(self, status_codes: List[QuEraTaskStatusCode]) -> "RemoteBatch":
        # offline:
        new_results = OrderedDict()
        for task_number, task in self.tasks.items():
            if (task.task_id is not None) and (task._result_exists()):
                if task.task_result_ir.task_status in status_codes:
                    continue
            new_results[task_number] = task

        return RemoteBatch(new_results, self.name)

    def get_failed_tasks(self) -> "RemoteBatch":
        # offline:
        new_task_results = OrderedDict()
        for task_number, task in self.tasks.items():
            if (task.task_id is not None) and (task._result_exists()):
                if task.task_result_ir.task_status in [
                    QuEraTaskStatusCode.Failed,
                    QuEraTaskStatusCode.Unaccepted,
                ]:
                    new_task_results[task_number] = task

        return RemoteBatch(new_task_results, name=self.name)

    def remove_failed_tasks(self) -> "RemoteBatch":
        # offline:
        new_results = OrderedDict()
        for task_number, task in self.tasks.items():
            if (task.task_id is not None) and (task._result_exists()):
                if task.task_result_ir.task_status in [
                    QuEraTaskStatusCode.Failed,
                    QuEraTaskStatusCode.Unaccepted,
                ]:
                    continue
            new_results[task_number] = task

        return RemoteBatch(new_results, self.name)

    def get_finished_tasks(self) -> "RemoteBatch":
        # offline
        new_results = OrderedDict()
        for task_number, task in self.tasks.items():
            if (task.task_id is not None) and (task._result_exists()):
                new_results[task_number] = task

        return RemoteBatch(new_results, self.name)

    def get_completed_tasks(self) -> "RemoteBatch":
        # offline
        new_results = OrderedDict()
        for task_number, task in self.tasks.items():
            if (task.task_id is not None) and (task._result_exists()):
                if task.task_result_ir.task_status == QuEraShotStatusCode.Completed:
                    new_results[task_number] = task

        return RemoteBatch(new_results, self.name)

    def report(self) -> "Report":
        ## this potentially can be specialize/disatch
        ## offline
        index = []
        data = []
        metas = []
        geos = []

        for task_number, task in self.tasks.items():
            ## fliter not existing results tasks:
            if (task.task_id is None) or (not task._result_exists()):
                continue

            ## filter has result but is not correctly completed.
            if not task.task_result_ir.task_status == QuEraTaskStatusCode.Completed:
                continue

            geometry = task.geometry
            perfect_sorting = "".join(map(str, geometry.filling))
            parallel_decoder = geometry.parallel_decoder

            if parallel_decoder:
                cluster_indices = parallel_decoder.get_cluster_indices()
            else:
                cluster_indices = {(0, 0): list(range(len(perfect_sorting)))}

            shot_iter = filter(
                lambda shot: shot.shot_status == QuEraShotStatusCode.Completed,
                task.result().shot_outputs,
            )

            for shot, (cluster_coordinate, cluster_index) in product(
                shot_iter, cluster_indices.items()
            ):
                pre_sequence = "".join(
                    map(
                        str,
                        (shot.pre_sequence[index] for index in cluster_index),
                    )
                )

                post_sequence = np.asarray(
                    [shot.post_sequence[index] for index in cluster_index],
                    dtype=np.int8,
                )

                pfc_sorting = "".join(
                    [perfect_sorting[index] for index in cluster_index]
                )

                key = (
                    task_number,
                    cluster_coordinate,
                    pfc_sorting,
                    pre_sequence,
                )

                index.append(key)
                data.append(post_sequence)
            metas.append(task.task_data.metadata)
            geos.append(task.geometry)

        index = pd.MultiIndex.from_tuples(
            index, names=["task_number", "cluster", "perfect_sorting", "pre_sequence"]
        )

        df = pd.DataFrame(data, index=index)
        df.sort_index(axis="index")

        rept = None
        if self.name is None:
            rept = Report(df, metas, geos, "Remote")
        else:
            rept = Report(df, metas, geos, self.name)

        return rept
