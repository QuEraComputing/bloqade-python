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
from dataclasses import dataclass
from bloqade.submission.ir.parallel import ParallelDecoder


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

    # do we need>?
    def _metadata(self) -> Dict[str, Number]:
        return {}

    # do we need>?
    @property
    def metadata(self) -> Dict[str, Number]:
        return self._metadata()

    @property
    def geometry(self) -> Geometry:
        return self._geometry()


class RemoteTask(Task):
    task_id: str

    def __init__(self, task_id: str):
        self.task_id = task_id

    def validate(self) -> None:
        raise NotImplementedError

    def result(self) -> QuEraTaskResults:
        # this methods hangs until the task is completed
        raise NotImplementedError

    def fetch(self) -> None:
        raise NotImplementedError

    def status(self) -> QuEraTaskStatusCode:
        raise NotImplementedError

    def pull(self) -> None:
        raise NotImplementedError

    def cancel(self) -> None:
        # this method cancels the task
        raise NotImplementedError

    def submit(self, force: bool):
        raise NotImplementedError

    def _result_exists(self) -> bool:
        raise NotImplementedError


class LocalTask(Task):
    def result(self):
        # need a new results type
        # for emulator jobs
        raise NotImplementedError

    def rerun(self, **kwargs):
        raise NotImplementedError


# Report is now just a helper class for
# organize and analysis data:
@dataclass
class Report:
    dataframe: pd.DataFrame

    def __init__(self, data) -> None:
        self.dataframe = data  # df
        self._bitstrings = None  # bitstring cache
        self._counts = None  # counts cache

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
