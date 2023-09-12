from bloqade.builder.typing import ScalarType
from beartype.typing import List, Tuple, Optional
from beartype import beartype
import numpy as np
from bloqade.ir.location.list import ListOfLocations
from bloqade.ir.location.base import LocationInfo, SiteFilling
from bloqade.ir.scalar import cast


class TransformTrait:
    @beartype
    def scale(self, scale: ScalarType) -> ListOfLocations:
        """scale the atom arrangement with a given factor"""

        scale = cast(scale)
        location_list = []
        for location_info in self.enumerate():
            x, y = location_info.position
            new_position = (scale * x, scale * y)
            location_list.append(
                LocationInfo(new_position, bool(location_info.filling.value))
            )

        return ListOfLocations(location_list)

    @beartype
    def add_position(
        self, position: Tuple[ScalarType, ScalarType], filled: bool = True
    ) -> "ListOfLocations":
        """add a position to existing atom arrangement."""

        from .list import ListOfLocations

        location_list = [LocationInfo(position, filled)]
        for location_info in self.enumerate():
            location_list.append(location_info)

        return ListOfLocations(location_list)

    @beartype
    def add_positions(
        self,
        positions: List[Tuple[ScalarType, ScalarType]],
        filling: Optional[List[bool]] = None,
    ) -> ListOfLocations:
        """add a list of positions to existing atom arrangement."""
        from .list import ListOfLocations

        location_list = []

        if filling:
            for position, filled in zip(positions, filling):
                location_list.append(LocationInfo(position, filled))

        else:
            for position in positions:
                location_list.append(LocationInfo(position, True))

        for location_info in self.enumerate():
            location_list.append(location_info)

        return ListOfLocations(location_list)

    @beartype
    def apply_defect_count(
        self, n_defects: int, rng: np.random.Generator = np.random.default_rng()
    ) -> ListOfLocations:
        """apply n_defects randomly to existing atom arrangement."""
        from .list import ListOfLocations

        location_list = []
        for location_info in self.enumerate():
            location_list.append(location_info)

        for _ in range(n_defects):
            idx = rng.integers(0, len(location_list))
            location_list[idx] = LocationInfo(
                location_list[idx].position,
                (False if location_list[idx].filling is SiteFilling.filled else True),
            )

        return ListOfLocations(location_list)

    @beartype
    def apply_defect_density(
        self,
        defect_probability: float,
        rng: np.random.Generator = np.random.default_rng(),
    ) -> "ListOfLocations":
        """apply defect_probability randomly to existing atom arrangement."""
        from .list import ListOfLocations

        p = min(1, max(0, defect_probability))
        location_list = []

        for location_info in self.enumerate():
            if rng.random() < p:
                location_list.append(
                    LocationInfo(
                        location_info.position,
                        (
                            False
                            if location_info.filling is SiteFilling.filled
                            else True
                        ),
                    )
                )
            else:
                location_list.append(location_info)

        return ListOfLocations(location_list=location_list)
