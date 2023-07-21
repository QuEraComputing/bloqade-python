# NOTE: this is only the basic report, we should provide
#      a way to customize the report class,
#      e.g result.plot() returns a `TaskPlotReport` class instead
from collections import OrderedDict
from itertools import product
from typing import List, Union, TYPE_CHECKING
import numpy as np

import pandas as pd
from bloqade.submission.ir.task_results import QuEraShotStatusCode, QuEraTaskResults
from numpy.typing import NDArray

if TYPE_CHECKING:
    from bloqade.task.base import BatchResult
    from bloqade.task.cloud_base import CloudTaskShotResults


class Report:
    def __init__(
        self, batch_result: Union["BatchResult", "CloudTaskShotResults"]
    ) -> None:
        self._batch_result = batch_result
        self._dataframe = None  # df cache
        self._bitstrings = None  # bitstring cache
        self._counts = None  # counts cache

    @property
    def batch_result(self) -> "BatchResult":
        return self._batch_result

    @property
    def quera_task_results(self) -> OrderedDict[int, QuEraTaskResults]:
        return OrderedDict(
            [
                (task_number, task_result.quera_task_result)
                for task_number, task_result in self.batch_result.task_results.items()
            ]
        )

    @property
    def dataframe(self) -> pd.DataFrame:
        if self._dataframe is not None:
            return self._dataframe

        self._dataframe = self._construct_dataframe()
        return self._dataframe

    def _construct_dataframe(self) -> pd.DataFrame:
        index = []
        data = []

        for task_number, task_result in self.batch_result.task_results.items():
            geometry = task_result.task.geometry
            perfect_sorting = "".join(map(str, geometry.filling))
            parallel_decoder = geometry.parallel_decoder

            if parallel_decoder:
                cluster_indices = parallel_decoder.get_cluster_indices()
            else:
                cluster_indices = {(0, 0): list(range(len(perfect_sorting)))}

            shot_iter = filter(
                lambda shot: shot.shot_status == QuEraShotStatusCode.Completed,
                task_result.quera_task_result.shot_outputs,
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

                key = (
                    task_number,
                    cluster_coordinate,
                    perfect_sorting,
                    pre_sequence,
                )

                index.append(key)
                data.append(post_sequence)

        index = pd.MultiIndex.from_tuples(
            index, names=["task_number", "cluster", "perfect_sorting", "pre_sequence"]
        )

        df = pd.DataFrame(data, index=index)
        df.sort_index(axis="index")

        return df

    @property
    def markdown(self) -> str:
        return self.dataframe.to_markdown()

    @property
    def bitstrings(self) -> List[NDArray]:
        if self._bitstrings is not None:
            return self._bitstrings
        self._bitstrings = self._construct_bitstrings()
        return self._bitstrings

    def _construct_bitstrings(self) -> List[NDArray]:
        perfect_sorting = self.dataframe.index.get_level_values("perfect_sorting")
        pre_sequence = self.dataframe.index.get_level_values("pre_sequence")
        filtered_df = self.dataframe[perfect_sorting == pre_sequence]
        task_numbers = filtered_df.index.get_level_values("task_number")

        n_atoms = len(perfect_sorting[0])
        bitstrings = [np.zeros((0, n_atoms)) for _ in range(task_numbers.max() + 1)]

        for task_number in task_numbers.unique():
            bitstrings[task_number] = filtered_df.loc[task_number, ...].to_numpy()

        return bitstrings

    @property
    def counts(self) -> List[OrderedDict[str, int]]:
        if self._counts is not None:
            return self._counts
        self._counts = self._construct_counts()
        return self._counts

    def _construct_counts(self) -> List[OrderedDict[str, int]]:
        counts = []
        for bitstring in self.bitstrings:
            output = np.unique(bitstring, axis=0, return_counts=True)
            counts.append(
                {
                    "".join(map(str, unique_bitstring)): bitstring_count
                    for unique_bitstring, bitstring_count in zip(*output)
                }
            )

        return counts

    def rydberg_densities(self) -> pd.Series:
        # TODO: implement nan for missing task numbers
        perfect_sorting = self.dataframe.index.get_level_values("perfect_sorting")
        pre_sequence = self.dataframe.index.get_level_values("pre_sequence")

        return 1 - (
            self.dataframe.loc[perfect_sorting == pre_sequence]
            .groupby("task_number")
            .mean()
        )
