from decimal import Decimal
from numbers import Real
from bloqade.builder.start import ProgramStart
from bloqade.ir.scalar import Scalar, Literal, cast
from pydantic.dataclasses import dataclass
from typing import List, Generator, Tuple, Optional, Any, TYPE_CHECKING, Union
import numpy as np
from enum import Enum
import plotext as pltxt
import sys
from bloqade.visualization.atom_arragement_visualize import get_atom_arrangement_figure
from bloqade.visualization.display import display_atom_arrangement

if TYPE_CHECKING:
    from .list import ListOfLocations


class SiteFilling(int, Enum):
    filled = 1
    vacant = 0


@dataclass
class LocationInfo:
    position: Tuple[Scalar, Scalar]
    filling: SiteFilling

    def __init__(self, position: Tuple[Any, Any], filled: bool):
        if filled:
            self.filling = SiteFilling.filled
        else:
            self.filling = SiteFilling.vacant

        self.position = tuple(cast(ele) for ele in position)


class AtomArrangement(ProgramStart):
    def __repr__(self) -> str:
        xs_filled, xs_vacant = [], []
        ys_filled, ys_vacant = [], []

        counter = 0
        for _, location_info in enumerate(self.enumerate()):
            counter += 1
            (x, y) = location_info.position
            if type(x) is not Literal or type(y) is not Literal:
                return repr(
                    list(self.enumerate())
                )  # default to standard print of internal contents
            else:
                if location_info.filling is SiteFilling.filled:
                    xs_filled.append(float(x.value))
                    ys_filled.append(float(y.value))
                else:
                    xs_vacant.append(float(x.value))
                    ys_vacant.append(float(y.value))

        if counter == 0:
            return repr(
                list(self.enumerate())
            )  # default to standard print of internal contents

        pltxt.clear_figure()
        pltxt.limit_size(False, False)
        pltxt.plot_size(80, 24)
        pltxt.canvas_color("default")
        pltxt.axes_color("default")
        pltxt.ticks_color("white")
        pltxt.title("Atom Positions")
        pltxt.xlabel("x (um)")
        pltxt.ylabel("y (um)")

        marker = "."
        if sys.stdout.encoding.lower().startswith("utf"):
            marker = "dot"

        pltxt.scatter(xs_filled, ys_filled, color=(100, 55, 255), marker=marker)
        if len(xs_vacant) > 0:
            pltxt.scatter(
                xs_vacant, ys_vacant, color="white", label="vacant", marker=marker
            )

        return pltxt.build()

    def enumerate(self) -> Generator[LocationInfo, None, None]:
        """enumerate all locations in the register."""
        raise NotImplementedError

    def figure(self, fig_kwargs=None, **assignments):
        """obtain a figure object from the atom arrangement."""
        return get_atom_arrangement_figure(self, fig_kwargs, **assignments)

    def show(self, **assignments) -> None:
        display_atom_arrangement(self, assignments)

    @property
    def n_atoms(self) -> int:
        """number of atoms in the register."""
        raise NotImplementedError

    @property
    def n_dims(self) -> int:
        """number of dimensions in the register."""
        raise NotImplementedError

    def scale(self, scale: Union[Real, Scalar, str, Decimal]) -> "ListOfLocations":
        """scale the atom arrangement with a given factor"""
        from .list import ListOfLocations

        scale = cast(scale)
        location_list = []
        for location_info in self.enumerate():
            x, y = location_info.position
            new_position = (scale * x, scale * y)
            location_list.append(
                LocationInfo(new_position, bool(location_info.filling.value))
            )

        return ListOfLocations(location_list)

    def add_position(
        self, position: Tuple[Any, Any], filled: bool = True
    ) -> "ListOfLocations":
        """add a position to existing atom arrangement."""

        from .list import ListOfLocations

        location_list = [LocationInfo(position, filled)]
        for location_info in self.enumerate():
            location_list.append(location_info)

        return ListOfLocations(location_list)

    def add_positions(
        self, positions: List[Tuple[Any, Any]], filling: Optional[List[bool]] = None
    ) -> "ListOfLocations":
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

    def apply_defect_count(
        self, n_defects: int, rng: np.random.Generator = np.random.default_rng()
    ) -> "ListOfLocations":
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


@dataclass(init=False)
class ParallelRegister(ProgramStart):
    """Parallel Register"""

    __match_args__ = ("_register", "_cluster_spacing")

    register_locations: List[List[Scalar]]
    register_filling: List[int]
    shift_vectors: List[List[Scalar]]

    def __init__(self, register: AtomArrangement, cluster_spacing: Any):
        self._register = register
        self._cluster_spacing = cluster_spacing

        if register.n_atoms > 0:
            # calculate bounding box
            # of this register
            location_iter = register.enumerate()
            (x, y) = next(location_iter).position
            x_min = x
            x_max = x
            y_min = y
            y_max = y

            for location_info in location_iter:
                (x, y) = location_info.position
                x_min = x.min(x_min)
                x_max = x.max(x_max)
                y_min = y.min(y_min)
                y_max = y.max(y_max)

            shift_x = (x_max - x_min) + cluster_spacing
            shift_y = (y_max - y_min) + cluster_spacing

            register_locations = [
                list(location_info.position) for location_info in register.enumerate()
            ]
            register_filling = [
                location_info.filling.value for location_info in register.enumerate()
            ]
            shift_vectors = [[shift_x, cast(0)], [cast(0), shift_y]]
        else:
            raise ValueError("No locations to parallelize.")

        self.register_locations = register_locations
        self.register_filling = register_filling
        self.shift_vectors = shift_vectors
        super().__init__(self)
