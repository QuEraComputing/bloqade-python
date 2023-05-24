from bloqade.builder.start import ProgramStart
from bloqade.ir.scalar import Scalar, cast
from pydantic.dataclasses import dataclass
from typing import List, Generator, Tuple, Any
from bokeh.plotting import show
import numpy as np
from enum import Enum
from bokeh.models import ColumnDataSource, Plot
from bokeh.plotting import figure


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
    def __init__(self) -> None:
        super().__init__(register=self)

    def enumerate(self) -> Generator[LocationInfo, None, None]:
        """enumerate all locations in the register."""
        raise NotImplementedError

    def figure(self, **assignments) -> Plot:
        xs_filled, ys_filled, labels_filled = [], [], []
        xs_vacant, ys_vacant, labels_vacant = [], [], []
        x_min = np.inf
        x_max = -np.inf
        y_min = np.inf
        y_max = -np.inf
        for idx, location_info in enumerate(self.enumerate()):
            (x_var, y_var) = location_info.position
            (x, y) = (x_var(**assignments), y_var(**assignments))
            x_min = min(x, x_min)
            y_min = min(y, y_min)
            x_max = max(x, x_max)
            y_max = max(y, y_max)
            if location_info.filling is SiteFilling.filled:
                xs_filled.append(x)
                ys_filled.append(y)
                labels_filled.append(idx)
            else:
                xs_vacant.append(x)
                ys_vacant.append(y)
                labels_vacant.append(idx)

        if self.n_atoms > 0:
            length_scale = max(y_max - y_min, x_max - x_min, 1)
        else:
            length_scale = 1

        source_filled = ColumnDataSource(
            data=dict(x=xs_filled, y=ys_filled, labels=labels_filled)
        )
        source_vacant = ColumnDataSource(
            data=dict(x=xs_vacant, y=ys_vacant, labels=labels_vacant)
        )
        p = figure(
            width=400,
            height=400,
            tools="hover,wheel_zoom,box_zoom,reset",
        )
        p.circle(
            "x", "y", source=source_filled, radius=0.015 * length_scale, fill_alpha=1
        )
        p.circle(
            "x",
            "y",
            source=source_vacant,
            radius=0.015 * length_scale,
            fill_alpha=0.25,
            color="grey",
            line_width=0.2 * length_scale,
        )

        return p

    def show(self, **assignments) -> None:
        """show the register."""
        show(self.figure(**assignments))

    @property
    def n_atoms(self) -> int:
        raise NotImplementedError

    @property
    def n_dims(self) -> int:
        raise NotImplementedError

    def parallelize(self, cluster_spacing: Any) -> "ParallelRegister":
        if self.n_atoms > 0:
            # calculate bounding box
            # of this register
            x_min = np.inf
            x_max = -np.inf
            y_min = np.inf
            y_max = -np.inf

            for location_info in self.enumerate():
                (x, y) = location_info.position
                x_min = x.min(x_min)
                x_max = x.max(x_max)
                y_min = y.min(y_min)
                y_max = y.max(y_max)

            shift_x = (x_max - x_min) + cluster_spacing
            shift_y = (y_max - y_min) + cluster_spacing

            register_locations = [
                list(location_info.position) for location_info in self.enumerate()
            ]
            register_filling = [
                location_info.filling.value for location_info in self.enumerate()
            ]

            return ParallelRegister(
                register_locations,
                register_filling,
                [[shift_x, cast(0)], [cast(0), shift_y]],
            )
        else:
            raise ValueError("No locations to parallelize.")


@dataclass(init=False)
class ParallelRegister(ProgramStart):
    register_locations: List[List[Scalar]]
    register_filling: List[int]
    shift_vectors: List[List[Scalar]]

    def __init__(
        self,
        register_sites: List[List[Scalar]],
        register_filling: List[int],
        shift_vectors: List[List[Scalar]],
    ):
        self.register_locations = register_sites
        self.register_filling = register_filling
        self.shift_vectors = shift_vectors
        super().__init__(register=self)
