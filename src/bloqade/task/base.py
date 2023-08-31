from collections import OrderedDict

import json
from typing import List, TextIO, Type, TypeVar, Union, Dict, Optional, Tuple
from numbers import Number

from pydantic import BaseModel
from bloqade.submission.ir.task_results import (
    QuEraTaskResults,
    QuEraTaskStatusCode,
)
from numpy.typing import NDArray
import pandas as pd
import numpy as np
from pydantic.dataclasses import dataclass
from bloqade.submission.ir.parallel import ParallelDecoder
from bloqade.visualization import report_visualize
from bokeh.io import show
import datetime

JSONSubType = TypeVar("JSONSubType", bound="JSONInterface")


@dataclass(frozen=True)
class Geometry:
    sites: List[Tuple[float, float]]
    filling: List[int]
    parallel_decoder: Optional[ParallelDecoder] = None


class JSONInterface(BaseModel):
    def json(self, exclude_none=True, by_alias=True, **json_options) -> str:
        return super().json(
            exclude_none=exclude_none, by_alias=by_alias, **json_options
        )

    def save_json(
        self, filename_or_io: Union[str, TextIO], mode="w", **json_options
    ) -> None:
        if isinstance(filename_or_io, str):
            with open(filename_or_io, mode) as f:
                f.write(self.json(**json_options))
        else:
            filename_or_io.write(self.json(**json_options))

    @classmethod
    def load_json(
        cls: Type[JSONSubType], filename_or_io: Union[str, TextIO]
    ) -> JSONSubType:
        if isinstance(filename_or_io, str):
            with open(filename_or_io, "r") as f:
                params = json.load(f)
        else:
            params = json.load(filename_or_io)

        return cls(**params)


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
        return [meta.get(field_name) for meta in self.metas]

    @property
    def markdown(self) -> str:
        return self.dataframe.to_markdown()

    def bitstrings(self, filter_perfect_filling: bool = True) -> List[NDArray]:
        perfect_sorting = self.dataframe.index.get_level_values("perfect_sorting")
        pre_sequence = self.dataframe.index.get_level_values("pre_sequence")
        if filter_perfect_filling:
            df = self.dataframe[perfect_sorting == pre_sequence]
        else:
            df = self.dataframe

        task_numbers = df.index.get_level_values("task_number").unique()

        bitstrings = []
        for task_number in task_numbers:
            bitstrings.append(df.loc[task_number, ...].to_numpy())

        return bitstrings

    @property
    def counts(self) -> List[OrderedDict[str, int]]:
        if self._counts is not None:
            return self._counts
        self._counts = self._construct_counts()
        return self._counts

    def _construct_counts(self) -> List[OrderedDict[str, int]]:
        counts = []
        for bitstring in self.bitstrings():
            output = np.unique(bitstring, axis=0, return_counts=True)

            count_list = [
                ("".join(map(str, bitstring)), count)
                for bitstring, count in zip(*output)
            ]
            count_list.sort(key=lambda x: x[1], reverse=True)
            count = OrderedDict(count_list)

            counts.append(count)

        return counts

    def rydberg_densities(self, filter_perfect_filling: bool = True) -> pd.Series:
        # TODO: implement nan for missing task numbers
        perfect_sorting = self.dataframe.index.get_level_values("perfect_sorting")
        pre_sequence = self.dataframe.index.get_level_values("pre_sequence")

        if filter_perfect_filling:
            df = self.dataframe[perfect_sorting == pre_sequence]
        else:
            df = self.dataframe

        return 1 - (df.groupby("task_number").mean())

    def show(self):
        dat = report_visualize.format_report_data(self)
        p = report_visualize.report_visual(*dat)
        show(p)
