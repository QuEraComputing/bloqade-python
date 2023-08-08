from pydantic.dataclasses import dataclass
from ..scalar import Scalar, cast
from .waveform import Waveform
from typing import Dict
from ..tree_print import Printer
from bokeh.plotting import figure, show
from bokeh.layouts import gridplot, row, layout
from bokeh.models.widgets import PreText
from bokeh.models import ColumnDataSource


__all__ = [
    "Field",
    "Location",
    "SpatialModulation",
    "Uniform",
    "RunTimeVector",
    "ScaledLocations",
]


@dataclass(frozen=True)
class Location:
    value: int

    def __repr__(self) -> str:
        ph = Printer()
        ph.print(self)
        return ph.get_value()

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)

    def __str__(self):
        return f"Location({str(self.value)})"

    def children(self):
        return []

    def print_node(self):
        return f"Location {self.value}"


@dataclass
class SpatialModulation:
    def __hash__(self) -> int:
        raise NotImplementedError

    def __repr__(self) -> str:
        ph = Printer()
        ph.print(self)
        return ph.get_value()

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)

    def _get_info(self, **assignment):
        return {}

    def figure(self, **assignment):
        raise NotImplementedError


@dataclass
class UniformModulation(SpatialModulation):
    def __hash__(self) -> int:
        return hash(self.__class__)

    def __str__(self):
        return "Uniform"

    def print_node(self):
        return "UniformModulation"

    def children(self):
        return []

    def figure(self, **assignment):
        p = figure(sizing_mode="stretch_both")
        p.text(
            x=[0.5],
            y=[0.5],
            text="Uniform",
            text_algin="center",
            text_baseline="middle",
        )
        return p

    def show(self, **assignment):
        show(self.figure(**assignment))


Uniform = UniformModulation()


@dataclass
class RunTimeVector(SpatialModulation):
    name: str

    def __hash__(self) -> int:
        return hash(self.name) ^ hash(self.__class__)

    def __str__(self):
        return f"RunTimeVector({str(self.name)})"

    def print_node(self):
        return "RunTimeVector"

    def children(self):
        return [self.name]

    def figure(self, **assginment):
        p = figure(sizing_mode="stretch_both")
        p.text(
            x=[0.5],
            y=[0.5],
            text=self.name,
            text_algin="center",
            text_baseline="middle",
        )
        return p

    def show(self, **assignment):
        show(self.figure(**assignment))


@dataclass(init=False)
class ScaledLocations(SpatialModulation):
    value: dict[Location, Scalar]

    def __init__(self, pairs):
        value = dict()
        for k, v in pairs.items():
            if isinstance(k, int):
                k = Location(k)
            elif isinstance(k, Location):
                pass
            else:
                raise ValueError(f"expected Location or int, got {k}")

            value[k] = cast(v)
        self.value = value

    def __hash__(self) -> int:
        return hash(frozenset(self.value.items())) ^ hash(self.__class__)

    def __str__(self):
        return f"ScaledLocations(value={str(self.value)})"

    def print_node(self):
        ## formatting location: scale pair:
        tmp = {f"{key.value}": val for key, val in self.value.items()}
        return f"ScaledLocations({str(tmp)})"

    def children(self):
        # can return list or dict
        # should return dict consisting of Location and Scalar
        annotated_children = {}
        for loc, scalar in self.value.items():
            annotated_children[loc.print_node()] = scalar

        return annotated_children

    def figure(self, **assignments):
        locs = []
        literal_val = []
        for k, v in self.value.items():
            locs.append(f"loc[{k.value}]")
            literal_val.append(float(v(**assignments)))

        print(locs)
        print(literal_val)
        source = ColumnDataSource(data=dict(locations=locs, yvals=literal_val))

        p = figure(
            y_range=locs, sizing_mode="stretch_both", x_axis_label="Scale factor"
        )
        p.hbar(y="locations", right="yvals", source=source, height=0.4)

        return p

    def show(self, **assignment):
        show(self.figure(**assignment))
        pass


@dataclass
class Field:
    """Field node in the IR. Which contains collection(s) of
    [`Waveform`][bloqade.ir.control.waveform.Waveform]

    ```bnf
    <field> ::= ('field' <spatial modulation>  <padded waveform>)*
    ```
    """

    value: Dict[SpatialModulation, Waveform]

    def __hash__(self) -> int:
        return hash(frozenset(self.value.items())) ^ hash(self.__class__)

    def __repr__(self) -> str:
        ph = Printer()
        ph.print(self)
        return ph.get_value()

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)

    def __str__(self):
        return f"Field({str(self.value)})"

    def add(self, other):
        if not isinstance(other, Field):
            raise ValueError(f"Cannot add Field and {other.__class__}")

        out = Field(dict(self.value))

        for spatial_modulation, waveform in other.value.items():
            if spatial_modulation in self.value:
                out.value[spatial_modulation] = out.value[spatial_modulation] + waveform
            else:
                out.value[spatial_modulation] = waveform

        return out

    def print_node(self):
        return "Field"

    def children(self):
        # return dict with annotations
        return {spatial_mod.print_node(): wf for spatial_mod, wf in self.value.items()}

    def figure(self, **assignments):
        full_figs = []
        idx = 0
        for spmod, wf in self.value.items():
            fig_mod = spmod.figure(**assignments)
            fig_wvfm = wf.figure(**assignments)

            # format AST tree:
            txt = wf.__repr__()
            txt = "> Waveform AST:\n" + txt

            txt_asgn = ""
            # format assignment:
            if len(assignments):
                txt_asgn = "> Assignments:\n"
                for key, val in assignments.items():
                    txt_asgn += f"{key} := {val}\n"
                txt_asgn += "\n"

            # Display AST tree:

            header = "Ch[%d]\n" % (idx)
            text_box = PreText(text=header + txt_asgn + txt, sizing_mode="stretch_both")
            text_box.styles = {"overflow": "scroll"}

            # layout channel:
            fp = gridplot(
                [[row(text_box, fig_mod, sizing_mode="stretch_both"), fig_wvfm]],
                merge_tools=False,
                sizing_mode="stretch_both",
            )
            fp.width_policy = "max"

            full_figs.append(fp)
            idx += 1

        full = layout(
            full_figs,
            # merge_tools=False,
            sizing_mode="stretch_both",
        )
        full.width_policy = "max"

        return full

    def show(self, **assignments):
        show(self.figure(**assignments))
