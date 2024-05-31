"""
This module defines classes and methods for managing and processing batches of tasks
in both local and remote contexts. The main classes provided are `LocalBatch` and 
`RemoteBatch`, which handle task execution, reporting, and error management.
"""

from decimal import Decimal
from numbers import Real
from collections import OrderedDict
from collections.abc import Sequence
from itertools import product
import traceback
import datetime
import sys
import os
import warnings
from dataclasses import dataclass, field
import pandas as pd
import numpy as np

from beartype.typing import Union, Optional, Dict, Any, List
from beartype import beartype

from bloqade.builder.typing import LiteralType
from bloqade.serialize import Serializer
from bloqade.task.base import Report
from bloqade.task.quera import QuEraTask
from bloqade.task.braket import BraketTask
from bloqade.task.braket_simulator import BraketEmulatorTask
from bloqade.task.bloqade import BloqadeTask

from bloqade.builder.base import Builder

from bloqade.submission.ir.task_results import (
    QuEraShotStatusCode,
    QuEraTaskStatusCode,
    QuEraTaskResults,
)

# from bloqade.submission.base import ValidationError


class Serializable:
    def json(self, **options) -> str:
        """
        Serialize the object to JSON string.

        Returns:
            str: JSON string

        """
        from bloqade import dumps

        return dumps(self, **options)


MetadataFilterType = Union[Sequence[LiteralType], Sequence[List[LiteralType]]]


class Filter:
    @beartype
    def filter_metadata(
        self, __match_any__: bool = False, **metadata: MetadataFilterType
    ) -> Union["LocalBatch", "RemoteBatch"]:
        """
        Create a Batch object that has tasks filtered based on the values of metadata.

        Args:
            __match_any__ (bool):
                If True, then a task will be included
                if it matches any of the metadata filters.
                If False, then a task will be included only if it
                matches all of the metadata filters. Defaults to False.
            **metadata (MetadataFilterType):
                The metadata to filter on.
                The keys are the metadata names and
                the values (as a set) are the values to filter on.
                The elements in the set can be Real, Decimal, Tuple[Real], or Tuple[Decimal].

        Returns:
            Union["LocalBatch", "RemoteBatch"]:
                A Batch object with the filtered tasks,
                either LocalBatch or RemoteBatch depending
                on the type of self.
        """

        def convert_to_decimal(element):
            if isinstance(element, list):
                return list(map(convert_to_decimal, element))
            elif isinstance(element, (Real, Decimal)):
                return Decimal(str(element))
            else:
                raise ValueError(
                    f"Invalid value {element} for metadata filter. "
                    "Only Real, Decimal, List[Real], and List[Decimal] "
                    "are supported."
                )

        def metadata_match_all(task):
            return all(
                task.metadata.get(key) in value for key, value in metadata.items()
            )

        def metadata_match_any(task):
            return any(
                task.metadata.get(key) in value for key, value in metadata.items()
            )

        metadata = {k: list(map(convert_to_decimal, v)) for k, v in metadata.items()}

        metadata_filter = metadata_match_any if __match_any__ else metadata_match_all

        new_tasks = OrderedDict(
            [(k, v) for k, v in self.tasks.items() if metadata_filter(v)]
        )

        kw = dict(self.__dict__)
        kw["tasks"] = new_tasks

        return self.__class__(**kw)


@dataclass
@Serializer.register
class LocalBatch(Serializable, Filter):
    source: Optional[Builder]
    tasks: OrderedDict[int, Union[BraketEmulatorTask, BloqadeTask]]
    name: Optional[str] = None

    def report(self) -> Report:
        """
        Generate analysis report based on currently completed tasks in the LocalBatch.

        Returns:
            Report: Analysis report.

        """
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

            metas.append(task.metadata)
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

    @beartype
    def rerun(
        self, multiprocessing: bool = False, num_workers: Optional[int] = None, **kwargs
    ):
        """
        Rerun all the tasks in the LocalBatch.

        Args:
            multiprocessing (bool): Whether to use multiprocessing. Defaults to False.
            num_workers (Optional[int]): Number of workers to use if multiprocessing.
                                        Defaults to None.
            **kwargs: Additional arguments to pass to the task run method.

        Returns:
            Report: Analysis report.

        """
        return self._run(
            multiprocessing=multiprocessing, num_workers=num_workers, **kwargs
        )

    def _run(
        self, multiprocessing: bool = False, num_workers: Optional[int] = None, **kwargs
    ):
        """
        Internal method to run tasks in the LocalBatch.

        Args:
            multiprocessing (bool): Whether to use multiprocessing. Defaults to False.
            num_workers (Optional[int]): Number of workers to use if multiprocessing.
                                        Defaults to None.
            **kwargs: Additional arguments to pass to the task run method.

        Raises:
            ValueError: If num_workers is specified but multiprocessing is not enabled.

        Returns:
            LocalBatch: Updated LocalBatch with run tasks.

        """
        if multiprocessing:
            from concurrent.futures import ProcessPoolExecutor as Pool

            with Pool(max_workers=num_workers) as pool:
                futures = OrderedDict()
                for task_number, task in enumerate(self.tasks.values()):
                    futures[task_number] = pool.submit(task.run, **kwargs)

                for task_number, future in futures.items():
                    self.tasks[task_number] = future.result()

        else:
            if num_workers is not None:
                raise ValueError(
                    "num_workers is only used when multiprocessing is enabled."
                )
            for task in self.tasks.values():
                task.run(**kwargs)

        return self


@LocalBatch.set_serializer
def _serialize(obj: LocalBatch) -> Dict[str, Any]:
    """
    Serialize LocalBatch object.

    Args:
        obj (LocalBatch): LocalBatch object to serialize.

    Returns:
        Dict[str, Any]: Serialized data.

    """
    return {
        "source": None,
        "tasks": [(k, v) for k, v in obj.tasks.items()],
        "name": obj.name,
    }


@LocalBatch.set_deserializer
def _deserializer(d: Dict[str, Any]) -> LocalBatch:
    """
    Deserialize data into LocalBatch object.

    Args:
        d (Dict[str, Any]): Data to deserialize.

    Returns:
        LocalBatch: Deserialized LocalBatch object.

    """
    d["tasks"] = OrderedDict(d["tasks"])
    return LocalBatch(**d)


@dataclass
@Serializer.register
class TaskError(Serializable):
    exception_type: str
    stack_trace: str


@dataclass
@Serializer.register
class BatchErrors(Serializable):
    task_errors: OrderedDict[int, TaskError] = field(
        default_factory=lambda: OrderedDict([])
    )

    @beartype
    def print_errors(self, task_indices: Union[List[int], int]) -> str:
        """
        Print errors for specified tasks.

        Args:
            task_indices (Union[List[int], int]): List of task indices or a single task index.

        Returns:
            str: Errors as string.

        """
        return str(self.get_errors(task_indices))

    @beartype
    def get_errors(self, task_indices: Union[List[int], int]):
        """
        Get errors for specified tasks.

        Args:
            task_indices (Union[List[int], int]): List of task indices or a single task index.

        Returns:
            BatchErrors: BatchErrors object containing the errors for specified tasks.

        """
        return BatchErrors(
            task_errors=OrderedDict(
                [
                    (task_index, self.task_errors[task_index])
                    for task_index in task_indices
                    if task_index in self.task_errors
                ]
            )
        )


@dataclass
@Serializer.register
class RemoteBatch(Filter):
    tasks: OrderedDict[int, Union[QuEraTask, BraketTask]]
    id: Optional[str] = None
    _errors: BatchErrors = field(default_factory=BatchErrors)
    name: Optional[str] = None
    _created_at: str = field(
        default_factory=lambda: datetime.datetime.now().isoformat()
    )
    _resolved_at: Optional[str] = None

    def report(self) -> Report:
        """
        Generate analysis report based on currently completed tasks in the RemoteBatch.

        Returns:
            Report: Analysis report.

        """
        metas = []
        geos = []

        def status(task):
            return task.result().status

        index = []
        data = []
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

            metas.append(task.metadata)
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

    def resolve(self):
        """
        Resolve tasks in the RemoteBatch.

        Raises:
            NotImplementedError: If task resolution is not implemented for a task.

        Returns:
            RemoteBatch: Updated RemoteBatch with resolved tasks.

        """
        for task_number, task in self.tasks.items():
            try:
                result = task.result()
                if result.status == QuEraTaskStatusCode.Complete:
                    continue

                if not result or (
                    result.status
                    in [QuEraTaskStatusCode.Pending, QuEraTaskStatusCode.Unknown]
                ):
                    task.resolve()

            except Exception:
                exc_type, exc_value, exc_tb = sys.exc_info()
                tb_str = "".join(traceback.format_tb(exc_tb))
                self._errors.task_errors[task_number] = TaskError(
                    exception_type=str(exc_type), stack_trace=tb_str
                )

        self._resolved_at = datetime.datetime.now().isoformat()
        return self

    def rerun(
        self,
        __rerun_all__: bool = False,
        multiprocessing: bool = False,
        num_workers: Optional[int] = None,
        **kwargs,
    ):
        """
        Rerun all tasks or failed tasks in the RemoteBatch.

        Args:
            __rerun_all__ (bool): If True, rerun all tasks.
                                  If False, rerun only failed tasks. Defaults to False.
            multiprocessing (bool): Whether to use multiprocessing. Defaults to False.
            num_workers (Optional[int]): Number of workers to use if multiprocessing.
                                         Defaults to None.
            **kwargs: Additional arguments to pass to the task run method.

        Returns:
            RemoteBatch: Updated RemoteBatch with rerun tasks.

        """
        return self._run(
            __rerun_all__=__rerun_all__,
            multiprocessing=multiprocessing,
            num_workers=num_workers,
            **kwargs,
        )

    def _run(
        self,
        __rerun_all__: bool = False,
        multiprocessing: bool = False,
        num_workers: Optional[int] = None,
        **kwargs,
    ):
        """
        Internal method to run tasks in the RemoteBatch.

        Args:
            __rerun_all__ (bool): If True, rerun all tasks. If False, rerun only failed tasks.
                                    Defaults to False.
            multiprocessing (bool): Whether to use multiprocessing. Defaults to False.
            num_workers (Optional[int]): Number of workers to use if multiprocessing.
                                        Defaults to None.
            **kwargs: Additional arguments to pass to the task run method.

        Raises:
            ValueError: If num_workers is specified but multiprocessing is not enabled.

        Returns:
            RemoteBatch: Updated RemoteBatch with run tasks.

        """
        if multiprocessing:
            from concurrent.futures import ProcessPoolExecutor as Pool

            with Pool(max_workers=num_workers) as pool:
                futures = OrderedDict()
                for task_number, task in enumerate(self.tasks.values()):
                    if (
                        not __rerun_all__
                        and task_number not in self._errors.task_errors
                    ):
                        continue

                    futures[task_number] = pool.submit(task.run, **kwargs)

                for task_number, future in futures.items():
                    self.tasks[task_number] = future.result()

        else:
            if num_workers is not None:
                raise ValueError(
                    "num_workers is only used when multiprocessing is enabled."
                )
            for task_number, task in self.tasks.items():
                if not __rerun_all__ and task_number not in self._errors.task_errors:
                    continue

                task.run(**kwargs)

        return self

    def print_errors(self, task_indices: Union[List[int], int]) -> str:
        """
        Print errors for specified tasks.

        Args:
            task_indices (Union[List[int], int]): List of task indices or a single task index.

        Returns:
            str: Errors as string.

        """
        return self._errors.print_errors(task_indices)

    def get_errors(self, task_indices: Union[List[int], int]):
        """
        Get errors for specified tasks.

        Args:
            task_indices (Union[List[int], int]): List of task indices or a single task index.

        Returns:
            BatchErrors: BatchErrors object containing the errors for specified tasks.

        """
        return self._errors.get_errors(task_indices)


@RemoteBatch.set_serializer
def _serialize_remote(obj: RemoteBatch) -> Dict[str, Any]:
    """
    Serialize RemoteBatch object.

    Args:
        obj (RemoteBatch): RemoteBatch object to serialize.

    Returns:
        Dict[str, Any]: Serialized data.

    """
    return {
        "tasks": [(k, v) for k, v in obj.tasks.items()],
        "id": obj.id,
        "name": obj.name,
        "created_at": obj._created_at,
        "resolved_at": obj._resolved_at,
        "errors": obj._errors,
    }


@RemoteBatch.set_deserializer
def _deserialize_remote(d: Dict[str, Any]) -> RemoteBatch:
    """
    Deserialize data into RemoteBatch object.

    Args:
        d (Dict[str, Any]): Data to deserialize.

    Returns:
        RemoteBatch: Deserialized RemoteBatch object.

    """
    d["tasks"] = OrderedDict(d["tasks"])
    d["errors"] = d.pop("errors")
    return RemoteBatch(**d)
