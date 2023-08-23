from bloqade.builder.start import ProgramStart
from bloqade.ir.scalar import Scalar, Literal, cast
from pydantic.dataclasses import dataclass
from typing import List, Generator, Tuple, Optional, Any, TYPE_CHECKING
from bokeh.plotting import show
import numpy as np
from enum import Enum
from bokeh.models import (
    ColumnDataSource,
    NumericInput,
    Button,
    Range1d,
    CustomJS,
    HoverTool,
)
from bokeh.plotting import figure
from bokeh.layouts import column, row
import plotext as pltxt

# from bokeh import events


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

        pltxt.scatter(xs_filled, ys_filled, color=(100, 55, 255), marker="dot")
        if len(xs_vacant) > 0:
            pltxt.scatter(
                xs_vacant, ys_vacant, color="white", label="vacant", marker="dot"
            )

        return pltxt.build()

    def enumerate(self) -> Generator[LocationInfo, None, None]:
        """enumerate all locations in the register."""
        raise NotImplementedError

    def figure(self, fig_kwargs=None, **assignments):
        """obtain a figure object from the atom arrangement."""
        xs_filled, ys_filled, labels_filled = [], [], []
        xs_vacant, ys_vacant, labels_vacant = [], [], []
        x_min = np.inf
        x_max = -np.inf
        y_min = np.inf
        y_max = -np.inf
        for idx, location_info in enumerate(self.enumerate()):
            (x_var, y_var) = location_info.position
            (x, y) = (float(x_var(**assignments)), float(y_var(**assignments)))
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

        # Ly = y_max - y_min
        # Lx = x_max - x_min
        # scale_x = (Lx+2)/(Ly+2)

        if self.n_atoms > 0:
            length_scale = max(y_max - y_min, x_max - x_min, 1)
        else:
            length_scale = 1

        source_filled = ColumnDataSource(
            data=dict(_x=xs_filled, _y=ys_filled, _labels=labels_filled)
        )
        source_vacant = ColumnDataSource(
            data=dict(_x=xs_vacant, _y=ys_vacant, _labels=labels_vacant)
        )
        source_all = ColumnDataSource(
            data=dict(
                _x=xs_vacant + xs_filled,
                _y=ys_vacant + ys_filled,
                _labels=labels_vacant + labels_filled,
            )
        )
        hover = HoverTool()
        hover.tooltips = [
            ("(x,y)", "(@_x, @_y)"),
            ("index: ", "@_labels"),
        ]

        ## remove box_zoom since we don't want to change the scale
        if fig_kwargs is None:
            fig_kwargs = {}

        p = figure(
            **fig_kwargs,
            width=400,
            height=400,
            tools="wheel_zoom,reset, undo, redo, pan",
            toolbar_location="above",
        )
        p.x_range = Range1d(x_min - 1, x_min + length_scale + 1)
        p.y_range = Range1d(y_min - 1, y_min + length_scale + 1)

        p.circle(
            "_x", "_y", source=source_filled, radius=0.015 * length_scale, fill_alpha=1
        )
        p.circle(
            "_x",
            "_y",
            source=source_vacant,
            radius=0.015 * length_scale,
            fill_alpha=0.25,
            color="grey",
            line_width=0.2 * length_scale,
        )

        p.circle(
            "_x",
            "_y",
            source=source_all,
            radius=0,  # in the same unit as the data
            fill_alpha=0,
            line_width=0.15 * length_scale,
            visible=True,  # display by default
            name="Brad",
        )
        p.add_tools(hover)

        return p

    def show(self, **assignments) -> None:
        """show the register."""
        p = self.figure(**assignments)

        # get the Blocade rad object
        cr = None
        for rd in p.renderers:
            if rd.name == "Brad":
                cr = rd

        # adding rydberg radis input
        Brad_input = NumericInput(
            value=0, low=0, title="Bloqade radius (um):", mode="float"
        )

        # js link toggle btn
        toggle_button = Button(label="Toggle")
        toggle_button.js_on_event(
            "button_click",
            CustomJS(args=dict(cr=cr), code="""cr.visible = !cr.visible;"""),
        )

        # js link radius
        Brad_input.js_link("value", cr.glyph, "radius")

        full = column(p, row(Brad_input, toggle_button))
        # full.sizing_mode="scale_both"
        show(full)

    @property
    def n_atoms(self) -> int:
        """number of atoms in the register."""
        raise NotImplementedError

    @property
    def n_dims(self) -> int:
        """number of dimensions in the register."""
        raise NotImplementedError

    def scale(self, scale: float | Scalar) -> "ListOfLocations":
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
