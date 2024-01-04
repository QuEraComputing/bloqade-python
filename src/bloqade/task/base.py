from collections import OrderedDict

from beartype.typing import List, Sequence, Union, Dict, Optional, Tuple
from beartype import beartype
from numbers import Number

from bloqade.submission.ir.task_results import (
    QuEraTaskResults,
    QuEraTaskStatusCode,
)
from numpy.typing import NDArray
import pandas as pd
import numpy as np
from pydantic.dataclasses import dataclass
from bloqade.submission.ir.parallel import ParallelDecoder
import datetime
from bloqade.visualization import display_report


@dataclass(frozen=True)
class Geometry:
    sites: List[Tuple[float, float]]
    filling: List[int]
    parallel_decoder: Optional[ParallelDecoder] = None


class Task:
    def _geometry(self) -> Geometry:
        raise NotImplementedError(
            f"{self.__class__.__name__}._geometry() not implemented"
        )

    @property
    def geometry(self) -> Geometry:
        return self._geometry()


class RemoteTask(Task):
    def validate(self) -> None:
        raise NotImplementedError

    def result(self) -> QuEraTaskResults:
        # online, Blocking
        # waiting for remote results to finish
        # return results
        raise NotImplementedError

    def fetch(self) -> None:
        # online, non-blocking
        # pull the result if they are complete
        raise NotImplementedError

    def status(self) -> QuEraTaskStatusCode:
        # online, non-blocking
        # probe current task status
        raise NotImplementedError

    def pull(self) -> None:
        # online, blocking
        # pull the current results
        raise NotImplementedError

    def cancel(self) -> None:
        # this method cancels the task
        raise NotImplementedError

    def submit(self, force: bool):
        # online, non-blocking
        # this method submit the task
        raise NotImplementedError

    def _result_exists(self) -> bool:
        raise NotImplementedError


class LocalTask(Task):
    def result(self):
        # need a new results type
        # for emulator jobs
        raise NotImplementedError

    def run(self, **kwargs):
        raise NotImplementedError


# Report is now just a helper class for
# organize and analysis data:
class Report:
    dataframe: pd.DataFrame
    metas: List[Dict]
    geos: List[Geometry]
    name: str = ""

    def __init__(self, data, metas, geos, name="") -> None:
        self.dataframe = data  # df
        self._bitstrings = None  # bitstring cache
        self._counts = None  # counts cache
        self.metas = metas
        self.geos = geos
        self.name = name + " " + str(datetime.datetime.now())

    def list_param(self, field_name: str) -> List[Union[Number, None]]:
        """
        List the parameters associate with the given variable field_name
        for each tasks.

        Args:
            field_name (str): variable name

        """

        def cast(x):
            if x is None:
                return None
            elif isinstance(x, (list, tuple, np.ndarray)):
                return list(map(cast, x))
            else:
                return float(x)

        return list(map(cast, (meta.get(field_name) for meta in self.metas)))

    @property
    def markdown(self) -> str:
        return self.dataframe.to_markdown()

    def _filter(
        self,
        *,
        task_number: Optional[int] = None,
        filter_perfect_filling: bool = True,
        clusters: Union[tuple[int, int], Sequence[Tuple[int, int]]] = [],
    ):
        mask = np.ones(len(self.dataframe), dtype=bool)

        if task_number is not None:
            task_numbers = self.dataframe.index.get_level_values("task_number")
            np.logical_and(task_numbers == task_number, mask, out=mask)

        if filter_perfect_filling:
            perfect_sorting = self.dataframe.index.get_level_values("perfect_sorting")
            pre_sequence = self.dataframe.index.get_level_values("pre_sequence")

            np.logical_and(perfect_sorting == pre_sequence, mask, out=mask)

        clusters = [clusters] if isinstance(clusters, tuple) else clusters

        for cluster in clusters:
            given_clusters = self.dataframe.index.get_level_values("cluster")
            np.logical_and(given_clusters == cluster, mask, out=mask)

        return mask

    @beartype
    def bitstrings(
        self,
        filter_perfect_filling: bool = True,
        clusters: Union[tuple[int, int], List[tuple[int, int]]] = [],
    ) -> List[NDArray]:
        """Get the bitstrings from the data.

        Args:
            filter_perfect_filling (bool): whether return will
            only contain perfect filling shots. Defaults to True.
            clusters: (tuple[int, int], Sequence[Tuple[int, int]]):
            cluster index to filter shots from. If none are provided
            all clusters are used, defaults to [].

        Returns:
            bitstrings (list of ndarray): list corresponding to each
            task in the report. Each element is an ndarray of shape
            (nshots, nsites) where nshots is the number of shots for
            the task and nsites is the number of sites in the task.

        Note:
            Note that nshots may vary between tasks if filter_perfect_filling
            is set to True.

        """

        task_numbers = self.dataframe.index.get_level_values("task_number").unique()

        bitstrings = []
        for task_number in task_numbers:
            mask = self._filter(
                task_number=task_number,
                filter_perfect_filling=filter_perfect_filling,
                clusters=clusters,
            )
            if np.any(mask):
                bitstrings.append(self.dataframe.loc[mask].to_numpy())
            else:
                bitstrings.append(
                    np.zeros((0, self.dataframe.shape[1]), dtype=np.uint8)
                )

        return bitstrings

    @beartype
    def counts(
        self,
        filter_perfect_filling: bool = True,
        clusters: Union[tuple[int, int], List[tuple[int, int]]] = [],
    ) -> List[OrderedDict[str, int]]:
        """Get the counts of unique bit strings.

        Args:
            filter_perfect_filling (bool): whether return will
            only contain perfect filling shots. Defaults to True.
            clusters: (tuple[int, int], Sequence[Tuple[int, int]]):
            cluster index to filter shots from. If none are provided
            all clusters are used, defaults to [].

        Returns:
            bitstrings (list of ndarray): list corresponding to each
            task in the report. Each element is an ndarray of shape
            (nshots, nsites) where nshots is the number of shots for
            the task and nsites is the number of sites in the task.

        Note:
            Note that nshots may vary between tasks if filter_perfect_filling
            is set to True.

        """

        def generate_counts(bitstring):
            output = np.unique(bitstring, axis=0, return_counts=True)

            count_list = [
                ("".join(map(str, bitstring)), count)
                for bitstring, count in zip(*output)
            ]
            count_list.sort(key=lambda x: x[1], reverse=True)
            count = OrderedDict(count_list)

            return count

        return list(
            map(generate_counts, self.bitstrings(filter_perfect_filling, clusters))
        )

    @beartype
    def rydberg_densities(
        self,
        filter_perfect_filling: bool = True,
        clusters: Union[tuple[int, int], List[tuple[int, int]]] = [],
    ) -> Union[pd.Series, pd.DataFrame]:
        """Get rydberg density for each task.

        Args:
            filter_perfect_filling (bool, optional): whether return will
            only contain perfect filling shots. Defaults to True.

        Return:
            per-site rydberg density for each task as a pandas DataFrame or Series.

        """
        mask = self._filter(
            filter_perfect_filling=filter_perfect_filling, clusters=clusters
        )
        df = self.dataframe[mask]
        return 1 - (df.groupby("task_number").mean())

    def show(self):
        """
        Interactive Visualization of the Report

        """
        display_report(self)
