from bloqade.ir.control.sequence import (
    RydbergLevelCoupling,
    HyperfineLevelCoupling,
)
from bloqade.emulator.sparse_operator import IndexMapping, Diagonal
from bloqade.emulator.space import (
    Space,
    SpaceType,
    LocalHilbertSpace,
    is_rydberg_state,
    is_hyperfine_state,
)
from scipy.sparse import csr_matrix
import numpy as np
from typing import Dict, Union
from numbers import Number

from bloqade.emulator.ir import RabiTerm, DetuningTerm, RabiOperatorType


def get_dtype(target_atoms: Dict[str, Number]):
    type_list = list(map(np.min_scalar_type, target_atoms.values()))
    return np.result_type(type_list)


def emit_two_level_rabi_index_map(info: RabiTerm) -> IndexMapping:
    match info:
        case RabiTerm(
            op_type=RabiOperatorType.RealValued,
            target_atoms=target_atoms,
            space=Space(
                space_type=SpaceType.FullSpace,
                configurations=configurations,
            ),
        ):
            (atom_index,) = target_atoms.keys()
            input_indices = configurations ^ (1 << atom_index)
            return IndexMapping(input_indices)

        case RabiTerm(
            op_type=RabiOperatorType.ComplexValued,
            target_atoms=target_atoms,
            space=Space(
                space_type=SpaceType.FullSpace,
                configurations=configurations,
            ),
        ):
            (atom_index,) = target_atoms.keys()
            output_indices = (configurations >> atom_index) & 1 == 1
            input_indices = configurations[output_indices] ^ (1 << atom_index)
            return IndexMapping(input_indices, output_indices)

        case RabiTerm(
            op_type=RabiOperatorType.RealValued,
            target_atoms=target_atoms,
            space=Space(
                space_type=SpaceType.SubSpace,
                configurations=configurations,
            ),
        ):
            (atom_index,) = target_atoms.keys()
            new_configurations = configurations ^ (1 << atom_index)
            input_indices = np.searchsorted(configurations, new_configurations)

            output_indices = input_indices < configurations.size
            input_indices = input_indices[output_indices]
            return IndexMapping(input_indices, output_indices)

        case RabiTerm(
            op_type=RabiOperatorType.ComplexValued,
            target_atoms=target_atoms,
            space=Space(
                space_type=SpaceType.SubSpace,
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

        case _:
            raise RuntimeError(
                "Fatal compilation error when lowering Rabi term to python."
            )


def emit_two_level_rabi_csr_matrix(info: RabiTerm) -> csr_matrix:
    shape = (info.space.size, info.space.size)
    dtype = get_dtype(info.target_atoms)
    match info:
        case RabiTerm(
            op_type=RabiOperatorType.RealValued,
            target_atoms=target_atoms,
            space=Space(
                space_type=SpaceType.FullSpace,
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

        case RabiTerm(
            op_type=RabiOperatorType.RealValued,
            target_atoms=target_atoms,
            space=Space(
                space_type=SpaceType.SubSpace,
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

        case RabiTerm(
            op_type=RabiOperatorType.ComplexValued,
            target_atoms=target_atoms,
            space=Space(
                space_type=SpaceType.FullSpace,
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

        case RabiTerm(
            op_type=RabiOperatorType.ComplexValued,
            target_atoms=target_atoms,
            space=Space(
                space_type=SpaceType.SubSpace,
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
            raise RuntimeError(
                "Fatal compilation error when lowering Rabi term to python."
            )


def emit_rabi_matrix(info: RabiTerm) -> Union[csr_matrix, IndexMapping]:
    match info:
        case RabiTerm(
            target_atoms=target_atoms,
            space=Space(n_level=LocalHilbertSpace.TwoLevel),
        ) if len(target_atoms) == 1:
            return emit_two_level_rabi_index_map(info)
        case RabiTerm(space=Space(n_level=LocalHilbertSpace.TwoLevel)):
            return emit_two_level_rabi_csr_matrix(info)
        case RabiTerm(
            space=Space(n_level=LocalHilbertSpace.ThreeLevel),
        ):
            raise NotImplementedError
        case _:
            raise RuntimeError(
                "Fatal compilation error when lowering Rabi term to python."
            )


def emit_detuning_matrix(info: DetuningTerm):
    match info:
        case DetuningTerm(
            target_atoms=target_atoms,
            level_coupling=HyperfineLevelCoupling(),
            space=Space(n_level=n_level, configurations=configurations),
        ):
            diagonal = np.zeros(configurations.size, dtype=get_dtype(target_atoms))
            for atom_index, detuning_value in target_atoms.items():
                mask = is_hyperfine_state(configurations, atom_index, n_level)
                diagonal[mask] += detuning_value

            return Diagonal(diagonal)

        case DetuningTerm(
            target_atoms=target_atoms,
            level_coupling=RydbergLevelCoupling(),
            space=Space(n_level=n_level, configurations=configurations),
        ):
            diagonal = np.zeros(configurations.size, dtype=get_dtype(target_atoms))
            for atom_index, detuning_value in target_atoms.items():
                mask = is_rydberg_state(configurations, atom_index, n_level)
                diagonal[mask] += detuning_value

            return Diagonal(diagonal)

        case _:
            raise RuntimeError(
                "Fatal compilation error when lowering Rabi term to python."
            )


def emit_rydberg_matrix(info: Union[RabiTerm, DetuningTerm], c6=5420441.13265):
    match info:
        case RabiTerm(
            space=Space(
                atom_coordinates=atom_coordinates,
                n_level=n_level,
                configurations=configurations,
            )
        ):
            diagonal = np.zeros(configurations.size, dtype=np.float64)

            for index_1, coordinate_1 in enumerate(atom_coordinates):
                coordinate_1 = np.asarray(coordinate_1)
                is_rydberg_1 = is_rydberg_state(configurations, index_1, n_level)
                for index_2, coordinate_2 in enumerate(
                    atom_coordinates[index_1 + 1 :], index_1 + 1
                ):
                    coordinate_2 = np.asarray(coordinate_2)
                    distance = np.linalg.norm(coordinate_1 - coordinate_2)

                    rydberg_interaction = c6 / (distance**6)

                    if rydberg_interaction <= np.finfo(np.float64).eps:
                        continue

                    mask = np.logical_and(
                        is_rydberg_1, is_rydberg_state(configurations, index_2, n_level)
                    )
                    diagonal[mask] += rydberg_interaction

            return Diagonal(diagonal)

        case DetuningTerm(
            space=Space(
                atom_coordinates=atom_coordinates,
                n_level=LocalHilbertSpace.TwoLevel,
                configurations=configurations,
            )
        ):
            diagonal = np.zeros(configurations.size, dtype=np.float64)

            for index_1, coordinate_1 in enumerate(atom_coordinates):
                coordinate_1 = np.asarray(coordinate_1)
                is_rydberg_1 = is_rydberg_state(configurations, index_1, n_level)
                for index_2, coordinate_2 in enumerate(
                    atom_coordinates[index_1 + 1 :], index_1 + 1
                ):
                    coordinate_2 = np.asarray(coordinate_2)
                    distance = np.linalg.norm(coordinate_1 - coordinate_2)

                    rydberg_interaction = c6 / (distance**6)

                    if rydberg_interaction <= np.finfo(np.float64).eps:
                        continue

                    mask = np.logical_and(
                        is_rydberg_1, is_rydberg_state(configurations, index_2, n_level)
                    )
                    diagonal[mask] += rydberg_interaction

            return Diagonal(diagonal)
