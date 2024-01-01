from bloqade.builder.typing import ScalarType
from bloqade.builder.start import ProgramStart
from bloqade.ir.scalar import Scalar, Literal, cast
from bloqade.ir.tree_print import Printer

from pydantic.dataclasses import dataclass
from beartype.typing import List, Tuple, Generator, Union, Optional
from beartype import beartype
from enum import Enum
from numpy.typing import NDArray
from bloqade.visualization import get_atom_arrangement_figure
from bloqade.visualization import display_ir

from beartype.vale import Is
from typing import Annotated
from plum import dispatch
import plotext as pltxt
import sys
import numpy as np


def check_position_array(array):
    return (
        array.ndim == 2
        and (
            np.issubdtype(array.dtype, np.floating)
            or np.issubdtype(array.dtype, np.integer)
        )
        and array.shape[1] == 2
    )


def check_bool_array(array):
    return array.ndim == 1 and np.issubdtype(array.dtype, np.bool_)


PositionArray = Annotated[np.ndarray, Is[check_position_array]]
BoolArray = Annotated[np.ndarray, Is[check_bool_array]]


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
class AtomArrangement(ProgramStart):
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

    @beartype
    def scale(self, scale: ScalarType):
        """
        Scale the geometry of your atoms.

        ### Usage Example:
        ```
        >>> reg = start.add_position([(0,0), (1,1)])
        # atom positions are now (0,0), (2,2)
        >>> new_reg = reg.scale(2)
        # you may also use scale on pre-defined geometries
        >>> from bloqade.atom_arrangement import Chain
        # atoms in the chain will now be 2 um apart versus
        # the default 1 um
        >>> Chain(11).scale(2)
        ```

        - Next possible steps are:
        - Continuing to build your geometry via:
            - `...add_position(positions).add_position(positions)`:
                to add more positions
            - `...add_position(positions).apply_defect_count(n_defects)`:
            to randomly drop out n_atoms
            - `...add_position(positions).apply_defect_density(defect_probability)`:
            to drop out atoms with a certain probability
            - `...add_position(positions).scale(scale)`: to scale the geometry
        - Targeting a level coupling once you're done with the atom geometry:
            - `...add_position(positions).rydberg`:
            to specify Rydberg coupling
            - `...add_position(positions).hyperfine`:
            to specify Hyperfine coupling
        - Visualizing your atom geometry:
            - `...add_position(positions).show()`:
            shows your geometry in your web browser

        """

        scale = cast(scale)
        location_list = []
        for location_info in self.enumerate():
            x, y = location_info.position
            new_position = (scale * x, scale * y)
            location_list.append(
                LocationInfo.create(new_position, bool(location_info.filling.value))
            )

        return ListOfLocations(location_list)

    @dispatch
    def _add_position(
        self, position: Tuple[ScalarType, ScalarType], filling: Optional[bool] = None
    ):
        if filling is None:
            filling = True

        location_list = list(self.enumerate())
        location_list.append(LocationInfo.create(position, filling))

        return ListOfLocations(location_list)

    @dispatch
    def _add_position(  # noqa: F811
        self,
        position: List[Tuple[ScalarType, ScalarType]],
        filling: Optional[List[bool]] = None,
    ):
        location_list = list(self.enumerate())

        assert (
            len(position) == len(filling) if filling else True
        ), "Length of positions and filling must be the same"

        if filling:
            for position, filling in zip(position, filling):
                location_list.append(LocationInfo.create(position, filling))

        else:
            for position in position:
                location_list.append(LocationInfo.create(position, True))

        return ListOfLocations(location_list)

    @dispatch
    def _add_position(  # noqa: F811
        self, position: PositionArray, filling: Optional[BoolArray] = None
    ):
        return self.add_position(
            list(map(tuple, position.tolist())),
            filling.tolist() if filling is not None else None,
        )

    def add_position(
        self,
        position: Union[
            PositionArray,
            List[Tuple[ScalarType, ScalarType]],
            Tuple[ScalarType, ScalarType],
        ],
        filling: Optional[Union[BoolArray, List[bool], bool]] = None,
    ) -> "ListOfLocations":
        """
        Add a position or multiple positions to a pre-existing geometry.

        `add_position` is capable of accepting:
        - A single tuple for one atom coordinate: `(1.0, 2.5)`
        - A list of tuples: `[(0.0, 1.0), (2.0,1.5), etc.]
        - A numpy array of shape (N, 2) where N is the number of atoms

        You may also intersperse variables anywhere a value may be present.

        You can also pass in an optional argument which determines the atom "filling"
        (whether or not at a specified coordinate an atom should be present).

        ### Usage Example:
        ```
        # single coordinate
        >>> reg = start.add_position((0,0))
        # you may chain add_position calls
        >>> reg_plus_two = reg.add_position([(2,2),(5.0, 2.1)])
        # you can add variables anywhere a value may be present
        >>> reg_with_var = reg_plus_two.add_position(("x", "y"))
        # and specify your atom fillings
        >>> reg_with_filling = reg_with_var.add_position([(3.1, 0.0), (4.1, 2.2)],
        [True, False])
        # alternatively you could use one boolean to specify
        # all coordinates should be empty/filled
        >>> reg_with_more_filling = reg_with_filling.add_positions([(3.1, 2.9),
        (5.2, 2.2)], False)
        ```

        - Next possible steps are:
        - Continuing to build your geometry via:
            - `...add_position(positions).add_position(positions)`:
                to add more positions
            - `...add_position(positions).apply_defect_count(n_defects)`:
            to randomly drop out n_atoms
            - `...add_position(positions).apply_defect_density(defect_probability)`:
            to drop out atoms with a certain probability
            - `...add_position(positions).scale(scale)`: to scale the geometry
        - Targeting a level coupling once you're done with the atom geometry:
            - `...add_position(positions).rydberg`: to specify Rydberg coupling
            - `...add_position(positions).hyperfine`: to specify Hyperfine coupling
        - Visualizing your atom geometry:
            - `...add_position(positions).show()`:
            shows your geometry in your web browser

        """
        return self._add_position(position, filling)

    @beartype
    def apply_defect_count(
        self, n_defects: int, rng: np.random.Generator = np.random.default_rng()
    ):
        """
        Drop `n_defects` atoms from the geometry randomly. Internally this occurs
        by setting certain sites to have a SiteFilling set to false indicating
        no atom is present at the coordinate.

        A default numpy-based Random Number Generator is used but you can
        explicitly override this by passing in your own.

        ### Usage Example:

        ```
        >>> from bloqade.atom_arrangement import Chain
        >>> import numpy as np
        # set a custom seed for a numpy-based RNG
        >>> custom_rng = np.random.default_rng(888)
        # randomly remove two atoms from the geometry
        >>> reg = Chain(11).apply_defect_count(2, custom_rng)
        # you may also chain apply_defect_count calls
        >>> reg.apply_defect_count(2, custom_rng)
        # you can also use apply_defect_count on custom geometries
        >>> from bloqade import start
        >>> start.add_position([(0,0), (1,1)]).apply_defect_count(1, custom_rng)
        ```

        - Next possible steps are:
        - Continuing to build your geometry via:
            - `...apply_defect_count(defect_counts).add_position(positions)`:
                to add more positions
            - `...apply_defect_count(defect_counts)
                .apply_defect_count(n_defects)`: to randomly drop out n_atoms
            - `...apply_defect_count(defect_counts)
                .apply_defect_density(defect_probability)`:
                to drop out atoms with a certain probability
            - `...apply_defect_count(defect_counts).scale(scale)`:
                to scale the geometry
        - Targeting a level coupling once you're done with the atom geometry:
            - `...apply_defect_count(defect_counts).rydberg`: to specify
                Rydberg coupling
            - `...apply_defect_count(defect_counts).hyperfine`:
                to specify Hyperfine coupling
        - Visualizing your atom geometry:
            - `...apply_defect_count(defect_counts).show()`:
                shows your geometry in your web browser
        """

        location_list = []
        for location_info in self.enumerate():
            location_list.append(location_info)

        filled_sites = []

        for index, location_info in enumerate(location_list):
            if location_info.filling is SiteFilling.filled:
                filled_sites.append(index)

        if n_defects >= len(filled_sites):
            raise ValueError(
                f"n_defects {n_defects} must be less than the number of filled sites "
                f"({len(filled_sites)})"
            )

        for _ in range(n_defects):
            index = rng.choice(filled_sites)
            location_list[index] = LocationInfo.create(
                location_list[index].position,
                (False if location_list[index].filling is SiteFilling.filled else True),
            )
            filled_sites.remove(index)

        return ListOfLocations(location_list)

    @beartype
    def apply_defect_density(
        self,
        defect_probability: float,
        rng: np.random.Generator = np.random.default_rng(),
    ):
        """
        Drop atoms randomly with `defect_probability` probability (range of 0 to 1).
        Internally this occurs by setting certain sites to have a SiteFilling
        set to false indicating no atom is present at the coordinate.

        A default numpy-based Random Number Generator is used but you can
        explicitly override this by passing in your own.

        ### Usage Example:

        ```
        >>> from bloqade.atom_arrangement import Chain
        >>> import numpy as np
        # set a custom seed for a numpy-based RNG
        >>> custom_rng = np.random.default_rng(888)
        # randomly remove two atoms from the geometry
        >>> reg = Chain(11).apply_defect_density(0.2, custom_rng)
        # you may also chain apply_defect_density calls
        >>> reg.apply_defect_count(0.1, custom_rng)
        # you can also use apply_defect_density on custom geometries
        >>> from bloqade import start
        >>> start.add_position([(0,0), (1,1)])
        .apply_defect_density(0.5, custom_rng)
        ```

        - Next possible steps are:
        - Continuing to build your geometry via:
            - `...apply_defect_count(defect_counts).add_position(positions)`:
            to add more positions
            - `...apply_defect_count(defect_counts).apply_defect_count(n_defects)`:
            to randomly drop out n_atoms
            - `...apply_defect_count(defect_counts)
            .apply_defect_density(defect_probability)`:
            to drop out atoms with a certain probability
            - `...apply_defect_count(defect_counts).scale(scale)`:
            to scale the geometry
        - Targeting a level coupling once you're done with the atom geometry:
            - `...apply_defect_count(defect_counts).rydberg`:
            to specify Rydberg coupling
            - `...apply_defect_count(defect_counts).hyperfine`:
            to specify Hyperfine coupling
        - Visualizing your atom geometry:
            - `...apply_defect_count(defect_counts).show()`:
            shows your geometry in your web browser
        """

        p = min(1, max(0, defect_probability))
        location_list = []

        for location_info in self.enumerate():
            if rng.random() < p:
                location_list.append(
                    LocationInfo.create(
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

    def remove_vacant_sites(self):
        new_locations = []
        for location_info in self.enumerate():
            if location_info.filling is SiteFilling.filled:
                new_locations.append(location_info)

        return ListOfLocations(new_locations)


@dataclass
class ParallelRegister(ProgramStart):
    atom_arrangement: AtomArrangement
    cluster_spacing: Scalar

    @property
    def n_atoms(self):
        return self.atom_arrangement.n_atoms

    @property
    def n_sites(self):
        return self.atom_arrangement.n_sites

    @property
    def n_vacant(self):
        return self.atom_arrangement.n_vacant

    @property
    def n_dims(self):
        return self.atom_arrangement.n_dims

    def __str__(self):
        return "ParallelRegister:\n" + self.atom_arrangement.__str__()

    def figure(self, fig_kwargs=None, **assignments):
        from bloqade.compiler.rewrite.common import AssignBloqadeIR
        from bloqade.compiler.codegen.hardware import GenerateLattice
        from bloqade.submission.capabilities import get_capabilities

        capabilities = get_capabilities()

        assigned_self = AssignBloqadeIR(assignments).emit(self)
        lattice_data = GenerateLattice(capabilities).emit(assigned_self)

        list_of_locations = ListOfLocations()
        for site, filling in zip(lattice_data.sites, lattice_data.filling):
            list_of_locations = list_of_locations.add_position(site, filling == 1)

        return list_of_locations.figure(fig_kwargs)

    def show(self, **assignments) -> None:
        display_ir(self, assignments)


@dataclass(init=False)
class ParallelRegisterInfo:
    """ParallelRegisterInfo"""

    register_locations: List[List[Scalar]]
    register_filling: List[int]
    shift_vectors: List[List[Scalar]]

    def __init__(self, parallel_register: ParallelRegister):
        atom_arrangement = parallel_register.atom_arrangement
        cluster_spacing = parallel_register.cluster_spacing

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


@dataclass(init=False)
class ListOfLocations(AtomArrangement):
    location_list: List[LocationInfo]

    @beartype
    def __init__(
        self,
        location_list: List[Union[LocationInfo, Tuple[ScalarType, ScalarType]]] = [],
    ):
        self.location_list = []
        for ele in location_list:
            if isinstance(ele, LocationInfo):
                self.location_list.append(ele)
            else:
                self.location_list.append(LocationInfo.create(ele, True))

        if self.location_list:
            self.__n_atoms = sum(
                1 for loc in self.location_list if loc.filling == SiteFilling.filled
            )
            self.__n_sites = len(self.location_list)
            self.__n_vacant = self.__n_sites - self.__n_atoms
            self.__n_dims = len(self.location_list[0].position)
        else:
            self.__n_sites = 0
            self.__n_atoms = 0
            self.__n_dims = None

        super().__init__()

    @property
    def n_atoms(self):
        return self.__n_atoms

    @property
    def n_sites(self):
        return self.__n_sites

    @property
    def n_vacant(self):
        return self.__n_vacant

    @property
    def n_dims(self):
        return self.__n_dims

    def enumerate(self):
        return iter(self.location_list)

    def __iter__(self):
        return iter(self.location_list)
