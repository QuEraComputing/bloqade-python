from dataclasses import dataclass
from numpy.typing import NDArray
from typing import List, Tuple, Union
import numpy as np
from enum import Enum


class SpaceType(str, Enum):
    FullSpace = "full_space"
    SubSpace = "sub_space"


class AtomType:
    def string_to_integer(self, fock_state: str) -> int:
        state_string = fock_state.replace("|", "").replace(">", "")

        state_int = 0
        shift = 1
        for local_state in state_string:
            state_int += shift * self.str_to_int[local_state]
            shift *= self.n_level.value

        return state_int

    def integer_to_string(self, state_int: int) -> str:
        state_string = ""
        local_state = state_int % self.n_level.value

        state_string = state_string + self.int_to_str[local_state]
        state_int //= self.n_level.value

        while state_int > 0:
            local_state = state_int % self.n_level.value

            state_string = state_string + self.int_to_str[local_state]
            state_int //= self.n_level.value

        if len(state_string) < self.n_atoms:
            state_string = state_string + "g" * (self.n_atoms - len(state_string))

        return f"|{state_string}>"

    def is_rydberg(self, configurations: NDArray, index: int) -> NDArray:
        return self.is_state(configurations, index, self.States.Rydberg)

    def swap_state(
        self, configurations: NDArray, index: int, state_1: int, state_2: int
    ) -> NDArray:
        raise NotImplementedError

    def transition_state(
        self, configurations: NDArray, index: int, fro: int, to: int
    ) -> NDArray:
        raise NotImplementedError


class ThreeLevelAtomType(AtomType):
    class States(int, Enum):
        Ground = 0
        Hyperfine = 1
        Rydberg = 2

    str_to_int = {"g": 0, "h": 1, "r": 2}
    int_to_str = ["g", "h", "r"]

    def is_state(self, configurations: NDArray, index: int, state: Union[States, int]):
        state = self.States(state)
        mask = (configurations // 3**index) % 3
        return mask == state.value

    def swap_state(
        self, configurations: NDArray, index: int, state_1: States, state_2: States
    ) -> NDArray:
        state_1 = self.States(state_1)
        state_2 = self.States(state_2)

        output = configurations.copy()

        mask_1 = self.is_state(configurations, index, state_1)
        mask_2 = self.is_state(configurations, index, state_2)
        delta = state_2.value - state_1.value

        output[mask_1] += delta * 3**index
        output[mask_2] -= delta * 3**index

        return output

    def transition_state(
        self, configurations: NDArray, index: int, fro: States, to: States
    ) -> NDArray:
        fro = self.States(fro)
        to = self.States(to)

        input_configs = self.is_state(configurations, index, fro)
        output_configs = configurations[input_configs]

        delta = to.value - fro.value
        return (input_configs, output_configs + (delta * 3**index))


class TwoLevelAtomType(AtomType):
    class States(int, Enum):
        Ground = 0
        Rydberg = 1

    str_to_int = {"g": 0, "r": 1}
    int_to_str = ["g", "r"]

    def is_state(self, configurations: NDArray, index: int, state: States):
        state = self.States(state)

        mask = configurations & (1 << index)

        if state == self.States.Ground:
            return np.logical_not(mask)

        return mask

    def swap_state(
        self, configurations: NDArray, index: int, state_1: States, state_2: States
    ) -> NDArray:
        state_1 = self.States(state_1)
        state_2 = self.States(state_2)
        return configurations ^ (1 << index)

    def transition_state(
        self, configurations: NDArray, index: int, fro: States, to: States
    ) -> NDArray:
        fro = self.States(fro)
        to = self.States(to)

        input_configs = self.is_state(configurations, index, fro)
        output_configs = configurations[input_configs]

        return (input_configs, output_configs ^ (1 << index))


ThreeLevelAtom = ThreeLevelAtomType()
TwoLevelAtom = TwoLevelAtomType()
AtomStateType = Union[ThreeLevelAtom.States, TwoLevelAtom.States]


@dataclass(frozen=True)
class Space:
    space_type: SpaceType
    atom_type: AtomType
    atom_coordinates: List[Tuple[float, float]]
    configurations: NDArray

    @staticmethod
    def create(
        atom_coordinates: List[Tuple[float, float]],
        n_level: Union[int, AtomType] = TwoLevelAtom,
        blockade_radius=0.0,
    ):
        atom_coordinates = [
            tuple([float(value) for value in coordinate])
            for coordinate in atom_coordinates
        ]

        n_atom = len(atom_coordinates)

        if n_level == 2:
            atom_type = TwoLevelAtom
            Ns = 1 << n_atom
        elif n_level == 3:
            atom_type = ThreeLevelAtom
            Ns = 3**n_atom

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

        configurations = np.arange(Ns, dtype=np.min_scalar_type(Ns - 1))

        if all(len(sub_list) == 0 for sub_list in check_atoms):
            return Space(
                SpaceType.FullSpace, atom_type, atom_coordinates, configurations
            )

        for index_1, indices in enumerate(check_atoms):
            # get which configurations are in rydberg state for the current index.
            rydberg_configs_1 = atom_type.is_rydberg(configurations, index_1)
            for index_2 in indices:  # loop over neighbors within blockade radius
                # get which configus have the neighbor with a rydberg excitation
                rydberg_configs_2 = atom_type.is_rydberg(configurations, index_2)
                # get which states do not violate constraint
                mask = np.logical_not(
                    np.logical_and(rydberg_configs_1, rydberg_configs_2)
                )
                # remove states that violate blockade constraint
                configurations = configurations[mask]
                rydberg_configs_1 = rydberg_configs_1[mask]

        return Space(SpaceType.SubSpace, atom_type, atom_coordinates, configurations)

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

    def swap_state(
        self, index: int, state_1: AtomStateType, state_2: AtomStateType
    ) -> NDArray:
        col_config = self.atom_type.swap_state(
            self.configurations, index, state_1, state_2
        )
        if self.space_type == SpaceType.FullSpace:
            return (slice(-1), col_config)
        else:
            col_indices = np.searchsorted(self.configurations, col_config)
            mask = col_indices < self.size
            col_indices = col_indices[mask]

            if not np.all(mask):
                row_indices = np.argwhere(mask).flatten()
            else:
                row_indices = slice(-1)

            return (row_indices, col_indices)

    def transition_state(
        self, index: int, fro: AtomStateType, to: AtomStateType
    ) -> NDArray:
        row_indices, col_config = self.atom_type.transition_state(
            self.configurations, index, fro, to
        )
        if self.space_type == SpaceType.FullSpace:
            return (row_indices, col_config)
        else:
            col_indices = np.searchsorted(self.configurations, col_config)
            mask = col_indices < self.size

            col_indices = col_indices[mask]
            row_indices = np.logical_and(row_indices, mask)

            return (row_indices, col_indices)

    def fock_state_to_index(self, fock_state: str) -> int:
        state_int = self.atom_type.string_to_integer(fock_state)
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
        match self.space_type:
            case SpaceType.FullSpace:
                return self.atom_type.integer_to_string(index)
            case SpaceType.SubSpace:
                return self.atom_type.integer_to_string(self.configurations[index])

    def zero_state(self, dtype=np.float64) -> NDArray:
        state = np.zeros(self.size, dtype=dtype)
        state[0] = 1.0
        return state

    def __str__(self):
        # TODO: update this to use unicode
        output = ""

        n_digits = len(str(self.size - 1))
        fmt = "{{index: >{}d}}. {{fock_state:s}}\n".format(n_digits)
        if self.size < 50:
            for index, state_int in enumerate(self.configurations):
                fock_state = self.atom_type.integer_to_string(state_int)
                output = output + fmt.format(index=index, fock_state=fock_state)

        else:
            for index, state_int in enumerate(self.configurations[:25]):
                fock_state = self.atom_type.integer_to_string(state_int)
                output = output + fmt.format(index=index, fock_state=fock_state)

            output += (n_digits * "  ") + "...\n"

            for index, state_int in enumerate(
                self.configurations[-25:], start=self.size - 25
            ):
                fock_state = self.atom_type.integer_to_string(state_int)
                output = output + fmt.format(index=index, fock_state=fock_state)

        return output
