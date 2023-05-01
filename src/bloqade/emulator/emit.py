from bloqade.ir.sequence import LevelCoupling
from bloqade.emulator.sparse_operator import IndexMapping, Diagonal
from bloqade.emulator.space import Space, SpaceType, LocalHilbertSpace
from pydantic.dataclasses import dataclass
from scipy.sparse import csr_matrix
from enum import Enum
import numpy as np
from typing import Dict
from numbers import Number
from src.bloqade.emulator.emit import emit_rabi_index_map


class RabiOperatorType(str, Enum):
    RealValued = "real_valued"
    ComplexValued = "complex_valued"


@dataclass
class RabiInfo:
    op_type: RabiOperatorType
    level_coupling: LevelCoupling
    target_atoms: Dict[int, Number]
    space: Space


def emit_rabi_index_map(info: RabiInfo) -> IndexMapping:
    match info:
        case RabiInfo(
            op_type=RabiOperatorType.RealValued,
            level_coupling=LevelCoupling.Rydberg,
            target_atoms=target_atoms,
            space=Space(
                space_type=SpaceType.FullSpace,
                n_level=LocalHilbertSpace.TwoLevel,
                configurations=configurations,
            ),
        ):
            (atom_index,) = target_atoms.keys()
            input_indices = configurations ^ (1 << atom_index)
            return IndexMapping(input_indices)

        case RabiInfo(
            op_type=RabiOperatorType.ComplexValued,
            level_coupling=LevelCoupling.Rydberg,
            target_atoms=target_atoms,
            space=Space(
                space_type=SpaceType.FullSpace,
                n_level=LocalHilbertSpace.TwoLevel,
                configurations=configurations,
            ),
        ):
            (atom_index,) = target_atoms.keys()
            output_indices = (configurations >> atom_index) & 1 == 1
            input_indices = configurations[output_indices] ^ (1 << atom_index)
            return IndexMapping(input_indices, output_indices)

        case RabiInfo(
            op_type=RabiOperatorType.RealValued,
            level_coupling=LevelCoupling.Rydberg,
            target_atoms=target_atoms,
            space=Space(
                space_type=SpaceType.SubSpace,
                n_level=LocalHilbertSpace.TwoLevel,
                configurations=configurations,
            ),
        ):
            (atom_index,) = target_atoms.keys()
            new_configurations = configurations ^ (1 << atom_index)
            input_indices = np.searchsorted(configurations, new_configurations)

            output_indices = input_indices < configurations.size
            input_indices = input_indices[output_indices]
            return IndexMapping(input_indices, output_indices)

        case RabiInfo(
            op_type=RabiOperatorType.ComplexValued,
            level_coupling=LevelCoupling.Rydberg,
            target_atoms=target_atoms,
            space=Space(
                space_type=SpaceType.SubSpace,
                n_level=LocalHilbertSpace.TwoLevel,
                configurations=configurations,
            ),
        ):
            (atom_index,) = target_atoms.keys()
            rydberg_states = (configurations >> atom_index) & 1 == 1
            new_configurations = configurations[rydberg_states] ^ (1 << atom_index)
            input_indices = np.searchsorted(configurations, new_configurations)

            nonzero_indices = input_indices < configurations.size
            output_indices = np.logical_and(rydberg_states, nonzero_indices)
            input_indices = input_indices[nonzero_indices]
            return IndexMapping(input_indices, output_indices)


def emit_rabi_csr_matrix(info: RabiInfo) -> csr_matrix:
    shape = (info.space.size, info.space.size)
    dtype = np.common_type(list(info.target_atoms.values()))
    match info:
        case RabiInfo(
            op_type=RabiOperatorType.RealValued,
            level_coupling=LevelCoupling.Rydberg,
            target_atoms=target_atoms,
            space=Space(
                space_type=SpaceType.FullSpace,
                n_level=LocalHilbertSpace.TwoLevel,
                configurations=configurations,
            ) as space,
        ):
            indptr = np.zeros(space.size + 1, dtype=space.index_type)
            indptr[1:] = len(target_atoms)

            np.cumsum(indptr, out=indptr)

            indices = np.zeros((space.size, len(target_atoms)), dtype=space.index_type)
            data = np.zeros((space.size, len(target_atoms)), dtype=dtype)

            for atom_index, value in target_atoms.items():
                input_indices = configurations ^ (1 << atom_index)
                indices[:, atom_index] = input_indices
                data[:, atom_index] = value

            return csr_matrix(
                (data.ravel(), indices.ravel(), indptr), shape=shape, dtype=dtype
            )

        case RabiInfo(
            op_type=RabiOperatorType.RealValued,
            level_coupling=LevelCoupling.Rydberg,
            target_atoms=target_atoms,
            space=Space(
                space_type=SpaceType.SubSpace,
                n_level=LocalHilbertSpace.TwoLevel,
                configurations=configurations,
            ) as space,
        ):
            indptr = np.zeros(configurations.size, dtype=space.index_type)

            nnz_values = indptr[1:]
            for atom_index, value in target_atoms.items():
                new_configurations = configurations ^ (1 << atom_index)
                input_indices = np.searchsorted(configurations, new_configurations)
                nnz_values[input_indices < configurations.size] += 1

            np.cumsum(indptr, out=indptr)

            indices = np.zeros((indptr[-1],), dtype=space.index_type)
            data = np.zeros((indptr[-1],), dtype=dtype)

            index = indptr[0:-1]
            for atom_index, value in target_atoms.items():
                new_configurations = configurations ^ (1 << atom_index)
                input_indices = np.searchsorted(configurations, new_configurations)

                input_indices = input_indices[input_indices < configurations.size]
                nonzero_index = index[input_indices]

                indices[nonzero_index] = input_indices
                data[nonzero_index] = value
                index[input_indices] += 1

            indptr[1:] = index
            indptr[0] = 0
            return csr_matrix((data, indices, indptr), shape=shape, dtype=dtype)

        case RabiInfo(
            op_type=RabiOperatorType.ComplexValued,
            level_coupling=LevelCoupling.Rydberg,
            target_atoms=target_atoms,
            space=Space(
                space_type=SpaceType.FullSpace,
                n_level=LocalHilbertSpace.TwoLevel,
                configurations=configurations,
            ) as space,
        ):
            indptr = np.zeros(space.size + 1, dtype=space.index_type)

            nnz_values = indptr[1:]
            for atom_index in target_atoms.keys():
                rydberg_states = (configurations >> atom_index) & 1 == 1
                input_indices = configurations[rydberg_states] ^ (1 << atom_index)
                nnz_values[input_indices] += 1

            np.cumsum(indptr, out=indptr)

            indices = np.zeros((indptr[-1],), dtype=space.index_type)
            data = np.zeros((indptr[-1],), dtype=dtype)

            index = indptr[0:-1]
            for atom_index, value in target_atoms.items():
                rydberg_states = (configurations >> atom_index) & 1 == 1
                input_indices = configurations[rydberg_states] ^ (1 << atom_index)

                nonzero_index = index[rydberg_states]
                indices[nonzero_index] = input_indices
                data[nonzero_index] = value
                index[input_indices] += 1

            return csr_matrix((data, indices, indptr), shape=shape, dtype=dtype)

        case RabiInfo(
            op_type=RabiOperatorType.ComplexValued,
            level_coupling=LevelCoupling.Rydberg,
            target_atoms=target_atoms,
            space=Space(
                space_type=SpaceType.SubSpace,
                n_level=LocalHilbertSpace.TwoLevel,
                configurations=configurations,
            ) as space,
        ):
            indptr = np.zeros(space.size + 1, dtype=space.index_type)

            nnz_values = indptr[1:]
            for atom_index, value in target_atoms.items():
                rydberg_states = (configurations >> atom_index) & 1 == 1

                new_configurations = configurations[rydberg_states] ^ (1 << atom_index)
                input_indices = np.searchsorted(configurations, new_configurations)
                input_indices = input_indices[input_indices < configurations.size]

                nnz_values[input_indices] += 1

            np.cumsum(indptr, out=indptr)

            indices = np.zeros((indptr[-1],), dtype=space.index_type)
            data = np.zeros((indptr[-1],), dtype=dtype)

            index = indptr[0:-1]
            for atom_index, value in target_atoms.items():
                rydberg_states = (configurations >> atom_index) & 1 == 1

                new_configurations = configurations[rydberg_states] ^ (1 << atom_index)
                input_indices = np.searchsorted(configurations, new_configurations)

                input_indices = input_indices[input_indices < configurations.size]
                nonzero_index = index[input_indices]

                indices[nonzero_index] = input_indices
                data[nonzero_index] = value
                index[input_indices] += 1

            indptr[1:] = index
            indptr[0] = 0
            return csr_matrix((data, indices, indptr), shape=shape, dtype=dtype)

        case _:
            raise NotImplementedError
