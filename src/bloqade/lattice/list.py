from .base import Lattice
from pydantic.dataclasses import dataclass
from typing import List, Tuple


@dataclass
class ListOfPosition(Lattice):
    value: List[Tuple[float, ...]]
