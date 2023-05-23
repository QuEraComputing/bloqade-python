from .base import AtomArrangement
from typing import List, Tuple


class ListOfLocations(AtomArrangement):
    def __init__(self, value: List[Tuple[float, ...]] = []):
        if not all(map(lambda x: len(x) == len(value[0]), value)):
            raise ValueError("all positions must have the same dimension")

        if value:
            self.__n_atoms = len(value)
            self.__n_dims = len(value[0])
        else:
            self.__n_atoms = 0
            self.__n_dims = None

        self.value = [tuple(ele) for ele in value]

        super().__init__()

    def append(self, position: Tuple[float, ...]):
        return ListOfLocations(self.value + [position])

    def extend(self, positions: List[Tuple[float, ...]]):
        return ListOfLocations(self.value + positions)

    @property
    def n_atoms(self):
        return self.__n_atoms

    @property
    def n_dims(self):
        return self.__n_dims

    def enumerate(self):
        return iter(self.value)
