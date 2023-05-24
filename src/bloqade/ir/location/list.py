from .base import AtomArrangement, SiteInfo, SiteFilling
from typing import List, Tuple, Optional


class ListOfLocations(AtomArrangement):
    def __init__(self, value: List[SiteInfo] = []):
        if not all(map(lambda x: len(x) == len(value[0]), value)):
            raise ValueError("all positions must have the same dimension")

        if value:
            self.__n_atoms = len(value)
            self.__n_dims = len(value[0])
        else:
            self.__n_atoms = 0
            self.__n_dims = None

        self.value = list(value)

        super().__init__()

    def add_position(self, position: Tuple[float, ...], filled: bool = True):
        if filled:
            new_site = SiteInfo(position=position)
        else:
            new_site = SiteInfo(position=position, filling=SiteFilling.vacant)

        return ListOfLocations(self.value + [new_site])

    def add_positions(
        self, positions: List[Tuple[float, ...]], filling: Optional[List[bool]] = None
    ):
        new_list = ListOfLocations(self.value)

        if filling:
            for position, filled in zip(positions, filling):
                new_list = new_list.add_position(position, filled=filling)

        else:
            for position in positions:
                new_list = new_list.add_position(position)

        return new_list

    @property
    def n_atoms(self):
        return self.__n_atoms

    @property
    def n_dims(self):
        return self.__n_dims

    def enumerate(self):
        return iter(self.value)


start = ListOfLocations()
