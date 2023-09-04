from dataclasses import dataclass
from numpy.typing import NDArray
from typing import Union, TYPE_CHECKING
import numpy as np
from enum import Enum

if TYPE_CHECKING:
    from .emulator import Geometry


class SpaceType(str, Enum):
    FullSpace = "full_space"
    SubSpace = "sub_space"


@dataclass(frozen=True)
class AtomType:
    def string_to_integer(self, fock_state: str) -> int:
        state_string = fock_state.replace("|", "").replace(">", "")

        state_int = 0
        shift = 1
        for local_state in state_string:
            state_int += shift * self.str_to_int[local_state]
            shift *= self.n_level

        return state_int

    def integer_to_string(self, state_int: int, n_atoms: int) -> str:
        state_string = ""
        local_state = state_int % self.n_level

        state_string = state_string + self.int_to_str[local_state]
        state_int //= self.n_level

        while state_int > 0:
            local_state = state_int % self.n_level

            state_string = state_string + self.int_to_str[local_state]
            state_int //= self.n_level

        if len(state_string) < n_atoms:
            state_string = state_string + "g" * (n_atoms - len(state_string))

        return f"|{state_string}>"

    def is_rydberg_at(self, configurations: NDArray, index: int) -> NDArray:
        return self.is_state_at(configurations, index, self.State.Rydberg)

    def swap_state_at(
        self, configurations: NDArray, index: int, state_1: int, state_2: int
    ) -> NDArray:
        raise NotImplementedError

    def transition_state_at(
        self, configurations: NDArray, index: int, fro: int, to: int
    ) -> NDArray:
        raise NotImplementedError

    def is_state_at(self, configurations: NDArray, index: int, state: int) -> NDArray:
        raise NotImplementedError

    def __hash__(self):
        return hash(self.__class__)


@dataclass(frozen=True)
class ThreeLevelAtomType(AtomType):
    n_level = 3
    str_to_int = {"g": 0, "h": 1, "r": 2}
    int_to_str = ["g", "h", "r"]

    class State(int, Enum):
        Ground = 0
        Hyperfine = 1
        Rydberg = 2

    def is_state_at(cls, configurations: NDArray, index: int, state):
        if not isinstance(state, cls.State):
            raise ValueError(f"state: {state} is not a valid state for {cls.__name__}.")

        mask = (configurations // 3**index) % 3
        return mask == state.value

    def swap_state_at(
        self, configurations: NDArray, index: int, state_1: State, state_2: State
    ) -> NDArray:
        state_1 = self.State(state_1)
        state_2 = self.State(state_2)

        output = configurations.copy()

        mask_1 = self.is_state_at(configurations, index, state_1)
        mask_2 = self.is_state_at(configurations, index, state_2)
        delta = state_2.value - state_1.value

        output[mask_1] += delta * 3**index
        output[mask_2] -= delta * 3**index

        np.logical_or(mask_1, mask_2, out=mask_1)

        return mask_1, output[mask_1]

    def transition_state_at(
        self, configurations: NDArray, index: int, fro: State, to: State
    ) -> NDArray:
        fro = self.State(fro)
        to = self.State(to)

        input_configs = self.is_state_at(configurations, index, fro)
        output_configs = configurations[input_configs]

        delta = to.value - fro.value
        return (input_configs, output_configs + (delta * 3**index))


@dataclass(frozen=True)
class TwoLevelAtomType(AtomType):
    n_level = 2
    str_to_int = {"g": 0, "r": 1}
    int_to_str = ["g", "r"]

    class State(int, Enum):
        Ground = 0
        Rydberg = 1

    def is_state_at(self, configurations: NDArray, index: int, state: State):
        state = self.State(state)

        mask = ((configurations >> index) & 1) == 1

        if state == self.State.Ground:
            return np.logical_not(mask)

        return mask

    def swap_state_at(
        self, configurations: NDArray, index: int, state_1: State, state_2: State
    ) -> NDArray:
        state_1 = self.State(state_1)
        state_2 = self.State(state_2)
        return slice(None), configurations ^ (1 << index)

    def transition_state_at(
        self, configurations: NDArray, index: int, fro: State, to: State
    ) -> NDArray:
        fro = self.State(fro)
        to = self.State(to)

        input_configs = self.is_state_at(configurations, index, fro)
        output_configs = configurations[input_configs]
        return (input_configs, output_configs ^ (1 << index))


ThreeLevelAtom = ThreeLevelAtomType()
TwoLevelAtom = TwoLevelAtomType()


@dataclass(frozen=True)
class Space:
    space_type: SpaceType
    atom_type: AtomType
    geometry: "Geometry"
    configurations: NDArray

    @staticmethod
    def create(
        geometry: "Geometry",
        n_level: Union[int, AtomType] = TwoLevelAtom,
        blockade_radius=0.0,
    ):
        positions = geometry.positions
        n_atom = len(positions)

        if isinstance(n_level, AtomType):
            atom_type = n_level
            Ns = atom_type.n_level**n_atom
        elif n_level == 2:
            atom_type = TwoLevelAtom
            Ns = 1 << n_atom
        elif n_level == 3:
            atom_type = ThreeLevelAtom
            Ns = 3**n_atom
        else:
            raise ValueError(f"n_level: {n_level} is not a valid n_level.")

        check_atoms = []

        for index_1, position_1 in enumerate(positions):
            position_1 = np.asarray(position_1)
            atoms = []
            for index_2, position_2 in enumerate(positions[index_1 + 1 :], index_1 + 1):
                position_2 = np.asarray(position_2)
                if np.linalg.norm(position_1 - position_2) <= blockade_radius:
                    atoms.append(index_2)

            check_atoms.append(atoms)

        configurations = np.arange(Ns, dtype=np.min_scalar_type(Ns - 1))

        if all(len(sub_list) == 0 for sub_list in check_atoms):
            return Space(SpaceType.FullSpace, atom_type, positions, configurations)

        for index_1, indices in enumerate(check_atoms):
            # get which configurations are in rydberg state for the current index.
            rydberg_configs_1 = atom_type.is_rydberg_at(configurations, index_1)
            for index_2 in indices:  # loop over neighbors within blockade radius
                # get which configus have the neighbor with a rydberg excitation
                rydberg_configs_2 = atom_type.is_rydberg_at(configurations, index_2)
                # get which states do not violate constraint
                mask = np.logical_not(
                    np.logical_and(rydberg_configs_1, rydberg_configs_2)
                )
                # remove states that violate blockade constraint
                configurations = configurations[mask]
                rydberg_configs_1 = rydberg_configs_1[mask]

        return Space(SpaceType.SubSpace, atom_type, positions, configurations)

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
        return len(self.geometry)

    @property
    def state_type(self) -> np.dtype:
        return np.result_type(np.uint32, np.min_scalar_type(self.configurations[-1]))

    def is_rydberg_at(self, index: int) -> NDArray:
        return self.atom_type.is_rydberg_at(self.configurations, index)

    def is_state_at(self, index: int, state: int):
        return self.atom_type.is_state_at(self.configurations, index, state)

    def swap_state_at(self, index: int, state_1: int, state_2: int) -> NDArray:
        row_indices, col_config = self.atom_type.swap_state_at(
            self.configurations, index, state_1, state_2
        )
        if self.space_type == SpaceType.FullSpace:
            return (row_indices, col_config)
        else:
            col_indices = np.searchsorted(self.configurations, col_config)

            mask = col_indices < self.size
            mask[mask] = col_config[mask] == self.configurations[col_indices[mask]]

            if not np.all(mask):
                if isinstance(row_indices, slice):
                    return mask, col_indices[mask]
                else:
                    return row_indices[mask], col_indices[mask]
            else:
                return row_indices, col_indices

    def transition_state_at(self, index: int, fro: int, to: int) -> NDArray:
        row_indices, col_config = self.atom_type.transition_state_at(
            self.configurations, index, fro, to
        )
        if self.space_type == SpaceType.FullSpace:
            return (row_indices, col_config)
        else:
            col_indices = np.searchsorted(self.configurations, col_config)
            mask = col_indices < self.size
            mask = np.logical_and(mask, col_config == self.configurations[col_indices])

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
                return self.atom_type.integer_to_string(index, self.n_atoms)
            case SpaceType.SubSpace:
                return self.atom_type.integer_to_string(
                    self.configurations[index], self.n_atoms
                )

    def zero_state(self, dtype=np.float64) -> NDArray:
        state = np.zeros(self.size, dtype=dtype)
        state[0] = 1.0
        return state

    def sample_state_vector(self, state_vector: NDArray, n_samples: int) -> NDArray:
        p = np.abs(state_vector) ** 2
        sampled_configs = np.random.choice(self.configurations, size=n_samples, p=p)

        sample_fock_states = np.empty((n_samples, self.n_atoms), dtype=np.uint8)

        for i in range(self.n_atoms):
            sample_fock_states[:, i] += sampled_configs % self.atom_type.n_level
            sampled_configs //= self.atom_type.n_level

    def __str__(self):
        # TODO: update this to use unicode
        output = ""

        n_digits = len(str(self.size - 1))
        fmt = "{{index: >{}d}}. {{fock_state:s}}\n".format(n_digits)
        if self.size < 50:
            for index, state_int in enumerate(self.configurations):
                fock_state = self.atom_type.integer_to_string(state_int, self.n_atoms)
                output = output + fmt.format(index=index, fock_state=fock_state)

        else:
            for index, state_int in enumerate(self.configurations[:25]):
                fock_state = self.atom_type.integer_to_string(state_int, self.n_atoms)
                output = output + fmt.format(index=index, fock_state=fock_state)

            output += (n_digits * "  ") + "...\n"

            for index, state_int in enumerate(
                self.configurations[-25:], start=self.size - 25
            ):
                fock_state = self.atom_type.integer_to_string(state_int, self.n_atoms)
                output = output + fmt.format(index=index, fock_state=fock_state)

        return output
