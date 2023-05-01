from pydantic.dataclasses import dataclass
from numpy.typing import NDArray
from typing import List, Tuple
import numpy as np
from enum import Enum


class LocalHilbertSpace(int, Enum):
    TwoLevel = 2
    ThreeLevel = 3


class SpaceType(str, Enum):
    FullSpace = "full_space"
    SubSpace = "sub_space"


@dataclass
class Space:
    space_type: SpaceType
    n_level: LocalHilbertSpace
    configurations: NDArray

    @property
    def index_type(self):
        if self.size < np.iinfo(np.int32).max:
            return np.int32
        else:
            return np.int64

    @property
    def size(self):
        return self.configurations.size

    @property
    def state_type(self):
        return np.result_type(np.uint32, np.min_scalar_type(self.configurations[-1]))

    def __init__(
        self,
        atom_coordinates: List[Tuple[float, float]],
        n_level: LocalHilbertSpace = LocalHilbertSpace.TwoLevel,
        blockade_radius=0.0,
    ):
        def is_rydberg_state(configurations, index, n_level):
            match n_level:
                case LocalHilbertSpace.TwoLevel:
                    return (configurations >> index) & 1 == 1
                case LocalHilbertSpace.ThreeLevel:
                    return (configurations // 3**index) % 2 == 2

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
            case LocalHilbertSpace.ThreeLevel:
                Ns = 3**n_atom

        configurations = np.arange(Ns, dtype=np.min_scalar_type(Ns - 1))

        if all(len(sub_list) == 0 for sub_list in check_atoms):
            super().__init__(SpaceType.FullSpace, n_level, configurations)
            return

        for index_1, indices in enumerate(check_atoms):
            # get which configurations are in rydberg state for the current index.
            rydberg_configs_1 = is_rydberg_state(configurations, index_1, n_level)
            for index_2 in indices:  # loop over neighbors within blockade radius
                # get which configus have the neighbor with a rydberg excitation
                rydberg_configs_2 = is_rydberg_state(configurations, index_2, n_level)
                # get which states do not violate constraint
                mask = np.logical_not(
                    np.logical_and(rydberg_configs_1, rydberg_configs_2)
                )
                # remove states that violate blockade constraint
                configurations = configurations[mask]
                rydberg_configs_1 = rydberg_configs_1[mask]

        super().__init__(SpaceType.SubSpace, n_level, configurations)
