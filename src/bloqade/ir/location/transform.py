from bloqade.builder.typing import ScalarType
from beartype.typing import List, Tuple, Optional, Union, TYPE_CHECKING
from beartype.vale import Is
from typing import Annotated
from beartype import beartype
from plum import dispatch
import numpy as np
from bloqade.ir.scalar import cast

if TYPE_CHECKING:
    from bloqade.ir.location.list import ListOfLocations


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


class TransformTrait:
    @beartype
    def scale(self, scale: ScalarType):
        """
        Scale the geometry of your atoms.

        Usage Example:
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
            - |_ `...add_position(positions).add_position(positions)`:
                to add more positions
            - |_ `...add_position(positions).apply_defect_count(n_defects)`:
            to randomly drop out n_atoms
            - |_ `...add_position(positions).apply_defect_density(defect_probability)`:
            to drop out atoms with a certain probability
            - |_ `...add_position(positions).scale(scale)`: to scale the geometry
        - Targeting a level coupling once you're done with the atom geometry:
            - |_ `...add_position(positions).rydberg`:
            to specify Rydberg coupling
            - |_ `...add_position(positions).hyperfine`:
            to specify Hyperfine coupling
        - Visualizing your atom geometry:
            - |_ `...add_position(positions).show()`:
            shows your geometry in your web browser

        """
        from .list import ListOfLocations
        from .base import LocationInfo

        scale = cast(scale)
        location_list = []
        for location_info in self.enumerate():
            x, y = location_info.position
            new_position = (scale * x, scale * y)
            location_list.append(
                LocationInfo(new_position, bool(location_info.filling.value))
            )

        return ListOfLocations(location_list)

    @dispatch
    def _add_position(
        self, position: Tuple[ScalarType, ScalarType], filling: Optional[bool] = None
    ):
        from .list import ListOfLocations
        from .base import LocationInfo

        if filling is None:
            filling = True

        location_list = list(self.enumerate())
        location_list.append(LocationInfo(position, filling))

        return ListOfLocations(location_list)

    @dispatch
    def _add_position(  # noqa: F811
        self,
        position: List[Tuple[ScalarType, ScalarType]],
        filling: Optional[List[bool]] = None,
    ):
        from .list import ListOfLocations
        from .base import LocationInfo

        location_list = list(self.enumerate())

        assert (
            len(position) == len(filling) if filling else True
        ), "Length of positions and filling must be the same"

        if filling:
            for position, filling in zip(position, filling):
                location_list.append(LocationInfo(position, filling))

        else:
            for position in position:
                location_list.append(LocationInfo(position, True))

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

        Usage Example:
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
            - |_ `...add_position(positions).add_position(positions)`:
                to add more positions
            - |_ `...add_position(positions).apply_defect_count(n_defects)`:
            to randomly drop out n_atoms
            - |_ `...add_position(positions).apply_defect_density(defect_probability)`:
            to drop out atoms with a certain probability
            - |_ `...add_position(positions).scale(scale)`: to scale the geometry
        - Targeting a level coupling once you're done with the atom geometry:
            - |_ `...add_position(positions).rydberg`: to specify Rydberg coupling
            - |_ `...add_position(positions).hyperfine`: to specify Hyperfine coupling
        - Visualizing your atom geometry:
            - |_ `...add_position(positions).show()`:
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

        Usage Example:

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
            - |_ `...apply_defect_count(defect_counts).add_position(positions)`:
                to add more positions
            - |_ `...apply_defect_count(defect_counts)
                .apply_defect_count(n_defects)`: to randomly drop out n_atoms
            - |_ `...apply_defect_count(defect_counts)
                .apply_defect_density(defect_probability)`:
                to drop out atoms with a certain probability
            - |_ `...apply_defect_count(defect_counts).scale(scale)`:
                to scale the geometry
        - Targeting a level coupling once you're done with the atom geometry:
            - |_ `...apply_defect_count(defect_counts).rydberg`: to specify
                Rydberg coupling
            - |_ `...apply_defect_count(defect_counts).hyperfine`:
                to specify Hyperfine coupling
        - Visualizing your atom geometry:
            - |_ `...apply_defect_count(defect_counts).show()`:
                shows your geometry in your web browser
        """
        from .list import ListOfLocations
        from .base import LocationInfo, SiteFilling

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
            location_list[index] = LocationInfo(
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

        Usage Example:

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
            - |_ `...apply_defect_count(defect_counts).add_position(positions)`:
            to add more positions
            - |_ `...apply_defect_count(defect_counts).apply_defect_count(n_defects)`:
            to randomly drop out n_atoms
            - |_ `...apply_defect_count(defect_counts)
            .apply_defect_density(defect_probability)`:
            to drop out atoms with a certain probability
            - |_ `...apply_defect_count(defect_counts).scale(scale)`:
            to scale the geometry
        - Targeting a level coupling once you're done with the atom geometry:
            - |_ `...apply_defect_count(defect_counts).rydberg`:
            to specify Rydberg coupling
            - |_ `...apply_defect_count(defect_counts).hyperfine`:
            to specify Hyperfine coupling
        - Visualizing your atom geometry:
            - |_ `...apply_defect_count(defect_counts).show()`:
            shows your geometry in your web browser
        """
        from .list import ListOfLocations
        from .base import LocationInfo, SiteFilling

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

    def remove_vacant_sites(self):
        from .base import SiteFilling
        from .list import ListOfLocations

        new_locations = []
        for location_info in self.enumerate():
            if location_info.filling is SiteFilling.filled:
                new_locations.append(location_info)

        return ListOfLocations(new_locations)
