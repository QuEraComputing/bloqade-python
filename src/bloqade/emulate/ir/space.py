from dataclasses import dataclass
from numpy.typing import NDArray
from typing import TYPE_CHECKING
import numpy as np
from enum import Enum

if TYPE_CHECKING:
    from .emulator import Register
    from .atom_type import AtomType


class SpaceType(str, Enum):
    FullSpace = "full_space"
    SubSpace = "sub_space"


@dataclass(frozen=True)
class Space:
    space_type: SpaceType
    atom_type: AtomType
    geometry: "Register"
    configurations: NDArray

    @staticmethod
    def create(
        register: "Register",
    ):
        sites = register.sites
        n_atom = len(sites)
        atom_type = register.atom_type
        blockade_radius = register.blockade_radius
        Ns = atom_type.n_level**n_atom

        check_atoms = []

        for index_1, site_1 in enumerate(sites):
            site_1 = np.asarray(site_1)
            atoms = []
            for index_2, site_2 in enumerate(sites[index_1 + 1 :], index_1 + 1):
                site_2 = np.asarray(site_2)
                if np.linalg.norm(site_1 - site_2) <= blockade_radius:
                    atoms.append(index_2)

            check_atoms.append(atoms)

        configurations = np.arange(Ns, dtype=np.min_scalar_type(Ns - 1))

        if all(len(sub_list) == 0 for sub_list in check_atoms):
            return Space(SpaceType.FullSpace, atom_type, sites, configurations)

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

        return Space(SpaceType.SubSpace, atom_type, sites, configurations)

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
