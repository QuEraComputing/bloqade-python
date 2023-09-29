from pydantic.dataclasses import dataclass
from bloqade.ir.location.base import AtomArrangement, LocationInfo, SiteFilling
from bloqade.builder.typing import ScalarType
from beartype.typing import List, Tuple, Union
from beartype import beartype


@dataclass(init=False)
class ListOfLocations(AtomArrangement):
    __match_args__ = ("location_list",)
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
                self.location_list.append(LocationInfo(ele, True))

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


start = ListOfLocations()
"""
A Program starting point, alias of empty [`ListOfLocations`][bloqade.ir.location.list.ListOfLocations].

Next possible steps to build your program are adding atom positions and addressing level couplings.

- Specify which level coupling to address with: 
    - |_ `start.rydberg`: for [`Rydberg`][bloqade.builder.coupling.Rydberg] Level coupling
    - |_ `start.hyperfine`: for [`Hyperfine`][bloqade.builder.coupling.Hyperfine] Level coupling
    - LOCKOUT: You cannot add atoms to your geometry after specifying level coupling.

- continue/start building your geometry with:
    - |_ `start.add_position()`: to add atom(s) to current register. It will accept:
        - A single coordinate, represented as a tuple (e.g. `(5,6)`) with a value that
          can either be:
            - integers: `(5,6)`
            - floats: `(5.1, 2.5)`
            - strings (for later variable assignment): `("x", "y")`
            - [`Scalar`][bloqade.ir.scalar.Scalar] objects: `(2*cast("x"), 5+cast("y"))`   
        - A list of coordinates, represented as a list of types mentioned previously.
        - A numpy array with shape (n, 2) where n is the total number of atoms
    - `.add_position()` will return another `ListOfLocations` you can build on.
"""
