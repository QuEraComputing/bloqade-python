from bloqade.ir.sequence import LevelCoupling
from bloqade.emulator.sparse_operator import PermMatrix, Diagonal
from bloqade.emulator.space import Space, FullSpace, SubSpace, LocalHilbertSpace
from scipy.sparse import csr_matrix
import numpy as np
from typing import Dict
from numbers import Number


def local_rabi_matrix(
    level_coupling: LevelCoupling, target_atoms: Dict[int, Number], space: Space
):
    shape = (space.size, space.size)
    dtype = np.common_type(list(target_atoms.values()))
    n_targets = len(target_atoms)

    match (level_coupling, space):
        case (
            LevelCoupling.Rydberg,
            FullSpace(n_level=LocalHilbertSpace.TwoLevel),
        ) if len(target_atoms) == 1:
            configurations = np.arange(space.size, dtype=space.index_type)
            (atom_index,) = target_atoms.keys()
            input_indices = configurations ^ (1 << atom_index)
            return PermMatrix(input_indices)

        case (
            LevelCoupling.Rydberg,
            SubSpace(n_level=LocalHilbertSpace.TwoLevel, configurations=configurations),
        ) if len(target_atoms) == 1:
            (atom_index,) = target_atoms.keys()
            new_configurations = configurations ^ (1 << atom_index)
            input_indices = np.searchsorted(configurations, new_configurations)

            output_indices = input_indices < configurations.size
            input_indices = input_indices[output_indices]
            return PermMatrix(input_indices, output_indices)

        case (LevelCoupling.Rydberg, FullSpace(n_level=LocalHilbertSpace.TwoLevel)):
            configurations = np.arange(space.size)
            indptr = np.zeros(configurations.size, dtype=space.index_type)
            indptr[1:] = n_targets

            np.cumsum(indptr, out=indptr)

            indices = np.zeros((space.size, n_targets), dtype=space.index_type)
            data = np.zeros((space.size, n_targets), dtype=dtype)

            for atom_index, value in target_atoms.items():
                input_indices = configurations ^ (1 << atom_index)
                indices[:, atom_index] = input_indices
                data[:, atom_index] = value

            return csr_matrix(
                (data.ravel(), indices.ravel(), indptr), shape=shape, dtype=dtype
            )

        case (LevelCoupling.Rydberg, SubSpace(n_level=LocalHilbertSpace.TwoLevel)):
            configurations = np.arange(space.size)
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

                input_indices = input_indices[output_indices < configurations.size]
                nonzero_index = index[input_indices]

                indices[nonzero_index] = input_indices
                data[nonzero_index] = value
                index[input_indices] += 1

            return csr_matrix((data, indices, indptr), shape=shape, dtype=dtype)

        case _:
            raise NotImplementedError
