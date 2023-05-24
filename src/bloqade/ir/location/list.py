from .base import AtomArrangement, LocationInfo
from typing import List, Tuple, Optional, Any


class ListOfLocations(AtomArrangement):
    def __init__(self, location_list: List[LocationInfo] = []):
        if location_list:
            self.__n_atoms = len(location_list)
            self.__n_dims = len(location_list[0].position)
        else:
            self.__n_atoms = 0
            self.__n_dims = None

        self.position_list = list(location_list)

        super().__init__()

    def add_position(self, position: Tuple[Any, Any], filled: bool = True):
        new_location = LocationInfo(position, filled)
        return ListOfLocations(self.position_list + [new_location])

    def add_positions(
        self, positions: List[Tuple[Any, Any]], filling: Optional[List[bool]] = None
    ):
        new_locations = []

        if filling:
            for position, filled in zip(positions, filling):
                new_locations.append(LocationInfo(position, filled))

        else:
            for position in positions:
                new_locations.append(LocationInfo(position, True))

        return ListOfLocations(self.position_list + new_locations)

    @property
    def n_atoms(self):
        return self.__n_atoms

    @property
    def n_dims(self):
        return self.__n_dims

    def enumerate(self):
        return iter(self.position_list)


start = ListOfLocations()
