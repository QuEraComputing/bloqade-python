from .base import AtomArrangement, LocationInfo
from typing import List, Tuple, Any, Union


class ListOfLocations(AtomArrangement):
    def __init__(self, location_list: List[Union[LocationInfo, Tuple[Any, Any]]] = []):
        self.location_list = []
        for ele in location_list:
            if isinstance(ele, LocationInfo):
                self.location_list.append(ele)
            else:
                self.location_list.append(LocationInfo(ele, True))

        if location_list:
            self.__n_atoms = len(self.location_list)
            self.__n_dims = len(self.location_list[0].position)
        else:
            self.__n_atoms = 0
            self.__n_dims = None

        super().__init__()

    @property
    def n_atoms(self):
        return self.__n_atoms

    @property
    def n_dims(self):
        return self.__n_dims

    def enumerate(self):
        return iter(self.location_list)


start = ListOfLocations()
"""
    - Program starting node
    - Possible Next <LevelCoupling>

        -> `start.rydberg`
            :: address rydberg level coupling

        -> `start.hyperfine`
            :: address hyperfine level coupling

    - Possible Next <AtomArragement>

        -> `start.add_locations(List[Tuple[int]])`
            :: add multiple atoms to current register

        -> `start.add_location(Tuple[int])`
            :: add atom to current register
"""
