from dataclasses import dataclass
from numpy.typing import NDArray
from typing import List, Tuple, Dict, Union
import numpy as np
from enum import Enum


class LocalHilbertSpace(int, Enum):
    TwoLevel = 2
    ThreeLevel = 3


class SpaceType(str, Enum):
    FullSpace = "full_space"
    SubSpace = "sub_space"


class ThreeLevelState(tuple, Enum):
    ground: 0
    hyperfine: 1
    rydberg: 2


class TwoLevelState(int, Enum):
    ground: 0
    rydberg: 1


def is_state(
    configurations: NDArray, index: int, state: Union[ThreeLevelState, TwoLevelState]
):
    match state:
        case TwoLevelState.ground:
            return ((configurations >> index) & 1) ^ 1
        case TwoLevelState.rydberg:
            return (configurations >> index) & 1
        case ThreeLevelState.ground:
            return (configurations // 3**index) % 3 == 0
        case ThreeLevelState.hyperfine:
            return (configurations // 3**index) % 3 == 1
        case ThreeLevelState.rydberg:
            return (configurations // 3**index) % 3 == 2


@dataclass(init=False)
class FockStateConverter:
    n_level: LocalHilbertSpace
    str_to_int: Dict[str, int]
    int_to_str: List[str]

    def __init__(self, n_level: LocalHilbertSpace):
        match n_level:
            case LocalHilbertSpace.TwoLevel:
                int_to_str = ["g", "r"]

            case LocalHilbertSpace.ThreeLevel:
                int_to_str = ["g", "h", "r"]

        str_to_int = {s: i for i, s in enumerate(int_to_str)}

        super().__init__(n_level=n_level, str_to_int=str_to_int, int_to_str=int_to_str)

    def string_to_integer(self, fock_state: str) -> int:
        state_string = fock_state.replace("|", "").replace(">", "")

        state_int = 0
        shift = 1
        for site, local_state in enumerate(state_string):
            state_int += shift * self.str_to_int[local_state]
            shift *= self.n_level.value

        return state_int

    def integer_to_string(self, state_int: int) -> str:
        state_string = ""
        while state_int > 0:
            local_state = state_int % self.n_level.value
            state_string = state_string + self.int_to_str[local_state]
            state_int /= self.n_level.value

        return f"|{state_string}>"


@dataclass(frozen=True)
class Space:
    space_type: SpaceType
    n_level: LocalHilbertSpace
    atom_coordinates: List[Tuple[float, float]]
    configurations: NDArray

    @staticmethod
    def create(
        atom_coordinates: List[Tuple[float, float]],
        n_level: LocalHilbertSpace = LocalHilbertSpace.TwoLevel,
        blockade_radius=0.0,
    ):
        atom_coordinates = [
            tuple([float(value) for value in coordinate])
            for coordinate in atom_coordinates
        ]

        n_atom = len(atom_coordinates)
        check_atoms = []

        for index_1, position_1 in enumerate(atom_coordinates):
            position_1 = np.asarray(position_1)
            atoms = []
            for index_2, position_2 in enumerate(
                atom_coordinates[index_1 + 1 :], index_1 + 1
            ):
                position_2 = np.asarray(position_2)
                if np.linalg.norm(position_1 - position_2) <= blockade_radius:
                    atoms.append(index_2)

            check_atoms.append(atoms)

        match n_level:
            case LocalHilbertSpace.TwoLevel:
                Ns = 2 << n_atom
                state = TwoLevelState.rydberg
            case LocalHilbertSpace.ThreeLevel:
                Ns = 3**n_atom
                state = ThreeLevelState.rydberg

        configurations = np.arange(Ns, dtype=np.min_scalar_type(Ns - 1))

        if all(len(sub_list) == 0 for sub_list in check_atoms):
            return Space(SpaceType.FullSpace, n_level, atom_coordinates, configurations)

        for index_1, indices in enumerate(check_atoms):
            # get which configurations are in rydberg state for the current index.
            rydberg_configs_1 = is_state(configurations, index_1, state)
            for index_2 in indices:  # loop over neighbors within blockade radius
                # get which configus have the neighbor with a rydberg excitation
                rydberg_configs_2 = is_state(configurations, index_2, state)
                # get which states do not violate constraint
                mask = np.logical_not(
                    np.logical_and(rydberg_configs_1, rydberg_configs_2)
                )
                # remove states that violate blockade constraint
                configurations = configurations[mask]
                rydberg_configs_1 = rydberg_configs_1[mask]

        return Space(SpaceType.SubSpace, n_level, atom_coordinates, configurations)

    @property
    def index_type(self) -> np.dtype:
        if self.size < np.iinfo(np.int32).max:
            return np.int32
        else:
            return np.int64

    @property
    def size(self) -> int:
        return self.configurations.size

    @property
    def n_atoms(self) -> int:
        return len(self.atom_coordinates)

    @property
    def state_type(self) -> np.dtype:
        return np.result_type(np.uint32, np.min_scalar_type(self.configurations[-1]))

    def fock_state_to_index(self, fock_state: str) -> int:
        converter = FockStateConverter(self.n_level)
        state_int = converter.string_to_integer(fock_state)
        match self.space_type:
            case SpaceType.FullSpace:
                return state_int
            case SpaceType.SubSpace:
                index = np.searchsorted(self.configurations, state_int)

                if state_int != self.configurations[index]:
                    raise ValueError(
                        "state: {fock_state} not in rydberg blockade subspace."
                    )

                return index
            case _:  # TODO: fix error message
                raise NotImplementedError

    def index_to_fock_state(self, index: int) -> str:
        converter = FockStateConverter(self.n_level)
        match self.space_type:
            case SpaceType.FullSpace:
                return converter.integer_to_string(index)
            case SpaceType.SubSpace:
                return converter.integer_to_string(self.configurations[index])

    def __str__(self):
        # TODO: update this to use unicode
        output = ""
        converter = FockStateConverter(self.n_level)
        if self.size < 50:
            for index, state_int in enumerate(self.configurations):
                fock_state = converter.integer_to_string(state_int)
                output = output + f"{index}. {fock_state}\n"

        else:
            for index, state_int in enumerate(self.configurations[:25]):
                fock_state = converter.integer_to_string(state_int)
                output = output + f"{index}. {fock_state}\n"

            output += "..."

            for index, state_int in enumerate(
                self.configurations[-25:], start=self.size - 25
            ):
                fock_state = converter.integer_to_string(state_int)
                output = output + f"{index}. {fock_state}\n"

        return output

    def zero_state(self) -> NDArray:
        state = np.zeros(self.size)
        state[0] = 1.0
