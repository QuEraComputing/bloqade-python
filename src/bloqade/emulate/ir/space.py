from dataclasses import dataclass
from numpy.typing import NDArray
from typing import TYPE_CHECKING
import numpy as np
from enum import Enum

if TYPE_CHECKING:
    from .emulator import Register
    from .atom_type import AtomType

MAX_PRINT_SIZE = 30


class SpaceType(str, Enum):
    FullSpace = "full_space"
    SubSpace = "sub_space"


@dataclass(frozen=True)
class Space:
    space_type: SpaceType
    atom_type: "AtomType"
    geometry: "Register"
    configurations: NDArray

    @classmethod
    def create(cls, register: "Register"):
        sites = register.sites
        n_atom = len(sites)
        atom_type = register.atom_type
        blockade_radius = register.blockade_radius
        Ns = atom_type.n_level**n_atom

        check_atoms = []

        for index_1, site_1 in enumerate(sites[1:], 1):
            site_1 = np.asarray(site_1)
            atoms = []
            for index_2, site_2 in enumerate(sites[: index_1 + 1]):
                site_2 = np.asarray(site_2)
                if np.linalg.norm(site_1 - site_2) <= blockade_radius:
                    atoms.append(index_2)

            check_atoms.append(atoms)

        min_int_type = np.min_scalar_type(Ns - 1)
        config_type = np.result_type(min_int_type, np.uint32)

        if all(len(sub_list) == 0 for sub_list in check_atoms):
            # default to 32 bit if smaller than 32 bit
            configurations = np.arange(Ns, dtype=config_type)
            return Space(SpaceType.FullSpace, atom_type, sites, configurations)

        states = np.arange(atom_type.n_level, dtype=config_type)
        configurations = states

        for index_1, indices in enumerate(check_atoms, 1):
            if len(indices) == 0:
                continue

            # loop over neighbors within blockade radius
            # find all non-blockaded configurations
            mask = np.logical_not(atom_type.is_rydberg_at(configurations, indices[0]))
            for index_2 in indices[1:]:
                is_not_rydberg = np.logical_not(
                    atom_type.is_rydberg_at(configurations, index_2)
                )
                np.logical_and(is_not_rydberg, mask, out=mask)

            non_blockaded = configurations[mask]
            np.logical_not(mask, out=mask)
            blockaded = configurations[mask]

            # add new configurations
            # add all configurations because none of the configs are blockading
            new_non_blockaded = np.kron(non_blockaded, np.ones_like(states)) + np.kron(
                np.ones_like(non_blockaded), states * atom_type.n_level**index_1
            )
            # add all but the rydberg state because some at least one is blockading
            new_blockaded = np.kron(blockaded, np.ones_like(states[:-1])) + np.kron(
                np.ones_like(blockaded), states[:-1] * atom_type.n_level**index_1
            )

            configurations = np.hstack((new_blockaded, new_non_blockaded))

        configurations.sort()

        return cls(SpaceType.SubSpace, atom_type, sites, configurations)

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
        return self.configurations.dtype

    def is_rydberg_at(self, index: int) -> NDArray:
        return self.atom_type.is_rydberg_at(self.configurations, index)

    def is_state_at(self, index: int, state: int):
        return self.atom_type.is_state_at(self.configurations, index, state)

    def swap_state_at(self, index: int, state_1: int, state_2: int) -> NDArray:
        row_indices, col_config = self.atom_type.swap_state_at(
            self.configurations, index, state_1, state_2
        )

        if not isinstance(row_indices, slice):
            row_indices = np.argwhere(row_indices).ravel()

        if self.space_type is SpaceType.FullSpace:
            return (row_indices, col_config)
        else:
            col_indices = np.searchsorted(self.configurations, col_config)
            mask = col_indices < self.size
            mask[mask] = col_config[mask] == self.configurations[col_indices[mask]]

            if not np.all(mask):
                if isinstance(row_indices, slice):
                    row_indices = np.arange(self.size)

                return row_indices[mask], col_indices[mask]
            else:
                return row_indices, col_indices

    def transition_state_at(self, index: int, fro: int, to: int) -> NDArray:
        row_indices, col_config = self.atom_type.transition_state_at(
            self.configurations, index, fro, to
        )

        if not isinstance(row_indices, slice):
            row_indices = np.argwhere(row_indices).ravel()

        if self.space_type is SpaceType.FullSpace:
            return (row_indices, col_config)
        else:
            col_indices = np.searchsorted(self.configurations, col_config)

            mask = col_indices < self.size
            col_indices = col_indices[mask]
            row_indices = row_indices[mask]

            mask = col_config[mask] == self.configurations[col_indices]
            col_indices = col_indices[mask]
            row_indices = row_indices[mask]

            return (row_indices, col_indices)

    def fock_state_to_index(self, fock_state: str) -> int:
        state_int = self.atom_type.string_to_integer(fock_state)
        if self.space_type is SpaceType.FullSpace:
            return state_int
        else:
            index = np.searchsorted(self.configurations, state_int)
            if index >= self.size or state_int != self.configurations[index]:
                raise ValueError(
                    "state: {fock_state} not in rydberg blockade subspace."
                )

            return index

    def index_to_fock_state(self, index: int) -> str:
        if index < 0 or index >= self.size:
            raise ValueError(f"index: {index} out of bounds.")

        if self.space_type is SpaceType.FullSpace:
            return self.atom_type.integer_to_string(index, self.n_atoms)
        else:
            return self.atom_type.integer_to_string(
                self.configurations[index], self.n_atoms
            )

    def zero_state(self, dtype=np.float64) -> NDArray:
        state = np.zeros(self.size, dtype=dtype)
        state[0] = 1.0
        return state

    def sample_state_vector(
        self, state_vector: NDArray, n_samples: int, project_hyperfine: bool = True
    ) -> NDArray:
        from .atom_type import ThreeLevelAtomType

        p = np.abs(state_vector) ** 2
        sampled_configs = np.random.choice(self.configurations, size=n_samples, p=p)

        sample_fock_states = np.empty((n_samples, self.n_atoms), dtype=np.uint8)

        for i in range(self.n_atoms):
            sample_fock_states[:, i] = sampled_configs % self.atom_type.n_level
            sampled_configs //= self.atom_type.n_level

        if project_hyperfine and isinstance(self.atom_type, ThreeLevelAtomType):
            sample_fock_states[sample_fock_states == 1] = 0
            sample_fock_states[sample_fock_states == 2] = 1

        return sample_fock_states

    def __str__(self):
        # TODO: update this to use unicode
        output = ""

        n_digits = len(str(self.size - 1))
        fmt = "{{index: >{}d}}. {{fock_state:s}}\n".format(n_digits)
        if self.size < MAX_PRINT_SIZE:
            for index, state_int in enumerate(self.configurations):
                fock_state = self.atom_type.integer_to_string(state_int, self.n_atoms)
                output = output + fmt.format(index=index, fock_state=fock_state)

        else:
            lower_index = MAX_PRINT_SIZE // 2 + (MAX_PRINT_SIZE % 2)
            upper_index = self.size - MAX_PRINT_SIZE // 2

            for index, state_int in enumerate(self.configurations[:lower_index]):
                fock_state = self.atom_type.integer_to_string(state_int, self.n_atoms)
                output = output + fmt.format(index=index, fock_state=fock_state)

            output += (n_digits * "  ") + "...\n"

            for index, state_int in enumerate(
                self.configurations[upper_index:], start=self.size - MAX_PRINT_SIZE // 2
            ):
                fock_state = self.atom_type.integer_to_string(state_int, self.n_atoms)
                output = output + fmt.format(index=index, fock_state=fock_state)

        return output
