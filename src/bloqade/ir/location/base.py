from bloqade.builder.typing import ScalarType
from bloqade.builder.start import ProgramStart
from bloqade.ir.scalar import Scalar, Literal, cast
from bloqade.ir.location.transform import TransformTrait
from bloqade.ir.tree_print import Printer

from pydantic.dataclasses import dataclass
from beartype.typing import List, Tuple, Generator
from beartype import beartype
from enum import Enum
import plotext as pltxt
import sys
import numpy as np
from numpy.typing import NDArray
from bloqade.visualization import get_atom_arrangement_figure
from bloqade.visualization import display_ir


class SiteFilling(int, Enum):
    filled = 1
    vacant = 0

    def print_node(self) -> str:
        return self.name

    def children(self) -> List:
        return []


@dataclass(frozen=True)
class LocationInfo:
    position: Tuple[Scalar, Scalar]
    filling: SiteFilling

    @beartype
    @staticmethod
    def create(position: Tuple[ScalarType, ScalarType], filled: bool):
        if filled:
            filling = SiteFilling.filled
        else:
            filling = SiteFilling.vacant

        position = tuple(cast(ele) for ele in position)

        return LocationInfo(position, filling)

    def print_node(self) -> str:
        return f"Location: {self.filling.name}"

    def children(self) -> List[Scalar]:
        return {"x": self.position[0], "y": self.position[1]}


@dataclass(init=False)
class AtomArrangement(ProgramStart, TransformTrait):
    def __str__(self) -> str:
        def is_literal(x):
            return isinstance(x, Literal)

        plot_results = all(
            is_literal(info.position[0]) and is_literal(info.position[1])
            for info in self.enumerate()
        )

        if plot_results:
            xs = [float(info.position[0].value) for info in self.enumerate()]
            ys = [float(info.position[1].value) for info in self.enumerate()]
            filling = [bool(info.filling.value) for info in self.enumerate()]
            xs_filled = [x for x, filled in zip(xs, filling) if filled]
            ys_filled = [y for y, filled in zip(ys, filling) if filled]
            xs_vacant = [x for x, filled in zip(xs, filling) if not filled]
            ys_vacant = [y for y, filled in zip(ys, filling) if not filled]

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
        else:
            ph = Printer()
            ph.print(self)
            return ph.get_value()

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)

    def print_node(self) -> str:
        return "AtomArrangement"

    def children(self) -> List[LocationInfo]:
        return list(self.enumerate())

    def enumerate(self) -> Generator[LocationInfo, None, None]:
        """enumerate all locations in the register."""
        raise NotImplementedError

    def figure(self, fig_kwargs=None, **assignments):
        """obtain a figure object from the atom arrangement."""
        return get_atom_arrangement_figure(self, fig_kwargs, **assignments)

    def show(self, **assignments) -> None:
        display_ir(self, assignments)

    def rydberg_interaction(self, **assignments) -> NDArray:
        """calculate the Rydberg interaction matrix.

        Args:
            **assignments: the values to assign to the variables in the register.

        Returns:
            NDArray: the Rydberg interaction matrix in the lower triangular form.

        """

        from bloqade.constants import RB_C6

        # calculate the Interaction matrix
        V_ij = np.zeros((self.n_sites, self.n_sites))
        for i, site_i in enumerate(self.enumerate()):
            pos_i = np.array([float(ele(**assignments)) for ele in site_i.position])

            for j, site_j in enumerate(self.enumerate()):
                if j >= i:
                    break  # enforce lower triangular form

                pos_j = np.array([float(ele(**assignments)) for ele in site_j.position])
                r_ij = np.linalg.norm(pos_i - pos_j)

                V_ij[i, j] = RB_C6 / r_ij**6

        return V_ij

    @property
    def n_atoms(self) -> int:
        """number of atoms (filled sites) in the register."""
        raise NotImplementedError

    @property
    def n_sites(self) -> int:
        """number of sites in the register."""
        raise NotImplementedError

    @property
    def n_vacant(self) -> int:
        """number of vacant sites in the register."""
        raise NotImplementedError

    @property
    def n_dims(self) -> int:
        """number of dimensions in the register."""
        raise NotImplementedError


@dataclass(init=False)
class ParallelRegisterInfo(ProgramStart):
    """Parallel Register"""

    __match_args__ = ("_register", "_cluster_spacing")

    register_locations: List[List[Scalar]]
    register_filling: List[int]
    shift_vectors: List[List[Scalar]]

    @beartype
    def __init__(self, atom_arrangement: AtomArrangement, cluster_spacing: ScalarType):
        self._register = atom_arrangement
        self._cluster_spacing = cast(cluster_spacing)

        if atom_arrangement.n_atoms > 0:
            # calculate bounding box
            # of this register
            location_iter = atom_arrangement.enumerate()
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
                list(location_info.position)
                for location_info in atom_arrangement.enumerate()
            ]
            register_filling = [
                location_info.filling.value
                for location_info in atom_arrangement.enumerate()
            ]
            shift_vectors = [[shift_x, cast(0)], [cast(0), shift_y]]
        else:
            raise ValueError("No locations to parallelize.")

        self.register_locations = register_locations
        self.register_filling = register_filling
        self.shift_vectors = shift_vectors
        super().__init__(self)


@dataclass()
class ParallelRegister:
    atom_arrangement: AtomArrangement
    cluster_spacing: Scalar

    @property
    def info(self) -> ParallelRegisterInfo:
        return ParallelRegisterInfo(self.atom_arrangement, self.cluster_spacing)
