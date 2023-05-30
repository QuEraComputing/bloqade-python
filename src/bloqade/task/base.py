from bloqade.submission.ir.task_results import (
    QuEraTaskResults,
    QuEraTaskStatusCode,
    QuEraShotStatusCode,
)
from bloqade.submission.ir.parallel import ParallelDecoder
from typing import List, Union, TextIO, Tuple, Optional
from numpy.typing import NDArray
from pydantic.dataclasses import dataclass
import pandas as pd
import json


class Task:
    def submit(self) -> "TaskFuture":
        raise NotImplementedError

    def run_validation(self) -> None:
        raise NotImplementedError


@dataclass(frozen=True)
class Geometry:
    sites: List[Tuple[float, float]]
    filling: List[int]
    parallel_decoder: Optional[ParallelDecoder]


class TaskFuture:
    @property
    def geometry(self) -> Geometry:
        return self.task_geometry()

    def task_geometry(self) -> Geometry:
        raise NotImplementedError

    @property
    def task_result(self) -> QuEraTaskResults:
        return self.fetch(cache=True)

    def fetch(self, cache=False) -> QuEraTaskResults:
        raise NotImplementedError

    def status(self) -> QuEraTaskStatusCode:
        raise NotImplementedError

    def cancel(self) -> None:
        raise NotImplementedError


class JSONInterface:
    def json(self, **json_options) -> str:
        raise NotImplementedError

    def init_from_dict(self, **params) -> None:
        raise NotImplementedError

    def save_json(
        self, filename_or_io: Union[str, TextIO], mode="w", **json_options
    ) -> None:
        if isinstance(filename_or_io, str):
            with open(filename_or_io, mode) as f:
                f.write(self.json(**json_options))
        else:
            filename_or_io.write(self.json(**json_options))

    def load_json(self, filename_or_io: Union[str, TextIO]) -> None:
        if isinstance(filename_or_io, str):
            with open(filename_or_io, "r") as f:
                params = json.load(f)
        else:
            params = json.load(filename_or_io)

        self.init_from_dict(**params)


class Job(JSONInterface):
    def submit(self) -> "Future":
        raise NotImplementedError


class Future(JSONInterface):
    def task_futures(self) -> List[TaskFuture]:
        raise NotImplementedError

    def report(self) -> "Report":
        return Report(self)

    def cancel(self) -> None:
        raise NotImplementedError


# NOTE: this is only the basic report, we should provide
#      a way to customize the report class,
#      e.g result.plot() returns a `TaskPlotReport` class instead
class Report:
    def __init__(self, future: Future) -> None:
        self._future = future
        self._perfect_filling = None
        self._dataframe = None  # df cache
        self._bitstring = None  # bitstring cache
        self._task_results = None  # task_ir cache

    @property
    def future(self) -> Future:
        return self._future

    @property
    def task_results(self) -> List[QuEraTaskResults]:
        if self._task_results:
            return self._task_results

        self._task_results = [
            task_future.task_result for task_future in self.future.task_futures()
        ]

        return self._task_results

    @property
    def dataframe(self) -> pd.DataFrame:
        if self._dataframe:
            return self._dataframe

        self._dataframe = self.construct_dataframe()
        return self._dataframe

    def construct_dataframe(self) -> pd.DataFrame:
        index = []
        data = []

        for task_number, task_future in enumerate(self.future.task_futures()):
            perfect_sorting = "".join(map(str, task_future.geometry.filling))
            parallel_decoder = task_future.geometry.parallel_decoder

            if parallel_decoder:
                cluster_indices = parallel_decoder.get_cluster_indices()

                for shot in filter(
                    lambda shot: shot.shot_status == QuEraShotStatusCode.Completed,
                    task_future.task_result.shot_outputs,
                ):
                    for cluster_coordinate, cluster_index in cluster_indices.items():
                        pre_sequence = "".join(
                            map(
                                str,
                                (shot.pre_sequence[index] for index in cluster_index),
                            )
                        )

                        post_sequence = [
                            shot.post_sequence[index] for index in cluster_index
                        ]

                        key = (
                            cluster_coordinate,
                            perfect_sorting,
                            pre_sequence,
                            task_number,
                        )
                        index.append(key)
                        data.append(post_sequence)

            else:
                for shot in filter(
                    lambda shot: shot.shot_status == QuEraShotStatusCode.Completed,
                    task_future.task_result.shot_outputs,
                ):
                    pre_sequence = "".join(map(str, shot.pre_sequence))
                    key = ((0, 0), perfect_sorting, pre_sequence, task_number)

                    index.append(key)
                    data.append(shot.post_sequence)

        index = pd.MultiIndex.from_tuples(
            index, names=["cluster", "perfect_sorting", "pre_sequence", "task_number"]
        )

        df = pd.DataFrame(data, index=index)
        df.sort_index(axis="index")

        return df

    @property
    def markdown(self) -> str:
        return self.dataframe.to_markdown()

    @property
    def bitstring(self) -> NDArray:
        if self._bitstring:
            return self._bitstring
        self._bitstring = self.construct_bitstring()
        return self._bitstring

    def construct_bitstring(self) -> NDArray:
        perfect_sorting = self.dataframe.index.get_level_values("perfect_sorting")
        pre_sequence = self.dataframe.index.get_level_values("pre_sequence")
        return self.dataframe.loc[perfect_sorting == pre_sequence].to_numpy().squeeze()

    def rydberg_densities(self) -> pd.Series:
        perfect_sorting = self.dataframe.index.get_level_values("perfect_sorting")
        pre_sequence = self.dataframe.index.get_level_values("pre_sequence")
        return (
            self.dataframe.loc[perfect_sorting == pre_sequence]
            .groupby("task_number")
            .mean()
        )
