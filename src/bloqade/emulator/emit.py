from bloqade.ir.control.sequence import (
    LevelCoupling,
    rydberg,
    hyperfine,
)
from bloqade.emulator.sparse_operator import IndexMapping, Diagonal
from bloqade.emulator.space import (
    Space,
    SpaceType,
    LocalHilbertSpace,
    is_rydberg_state,
    is_hyperfine_state,
)
from bloqade.emulator.ir import EmulatorProgram, LaserCoupling, DetuningTerm, RabiTerm
from scipy.sparse import csr_matrix, csc_matrix
import numpy as np
from typing import Dict, Union
from numbers import Number, Real

from bloqade.emulator.ir import RabiTerm, DetuningTerm, RabiOperatorType


class LowerRabiTerm:
    def __init__(self, space: Space):
        self.space = space
        self.phase = None
        self.amplitude = None
        self.level_coupling = None
        self.target_atoms = {}

    def emit_two_level_full_space_single_atom_real(self):
        ((atom_index, value),) = self.target_atoms.items()

        input_indices = self.space.configurations ^ (1 << atom_index)
        return [(lambda t: value * self.amplitude(t), IndexMapping(input_indices))]
    
    def emit_two_level_full_space_single_atom_complex(self):
        ((atom_index, value),) = self.target_atoms.items()
        
        output_indices = (self.space.configurations >> atom_index) & 1 == 1
        input_indices = self.space.configurations[output_indices] ^ (
            1 << atom_index
        )
        
        op = IndexMapping(input_indices, output_indices)

        return [
            (lambda t: value * self.amplitude(t) * np.exp(1j * self.phase(t)), op),
            (
                lambda t: value * self.amplitude(t) * np.exp(-1j * self.phase(t)),
                op.ajoint(),
            ),
        ]

    def emit_two_level_subspace_single_atom_real(self):
        ((atom_index, value),) = self.target_atoms.items()

        new_configurations = self.space.configurations ^ (1 << atom_index)
        input_indices = np.searchsorted(
            self.space.configurations, new_configurations
        )

        output_indices = input_indices < self.space.configurations.size
        input_indices = input_indices[output_indices]
        return [
            (
                lambda t: value * self.amplitude(t),
                IndexMapping(input_indices, output_indices),
            )
        ]
    
    def emit_two_level_subspace_single_atom_complex(self):
        ((atom_index, value),) = self.target_atoms.items()

        rydberg_states = (self.space.configurations >> atom_index) & 1 == 1
        new_configurations = self.space.configurations[rydberg_states] ^ (
            1 << atom_index
        )
        input_indices = np.searchsorted(
            self.space.configurations, new_configurations
        )

        nonzero_indices = input_indices < self.space.size
        output_indices = np.logical_and(rydberg_states, nonzero_indices)
        input_indices = input_indices[nonzero_indices]
        op = IndexMapping(input_indices, output_indices)
        return [
            (lambda t: value * self.amplitude(t) * np.exp(1j * self.phase(t)), op),
            (
                lambda t: value * self.amplitude(t) * np.exp(-1j * self.phase(t)),
                op.ajoint(),
            ),
        ]

    def emit_two_level_full_space_multi_atom_real(self):
        shape = (self.space.size, self.space.size)
        indptr = np.zeros(self.space.size + 1, dtype=self.space.index_type)
        indptr[1:] = len(self.target_atoms)

        np.cumsum(indptr, out=indptr)

        indices = np.zeros(
            (self.space.size, len(self.target_atoms)), dtype=self.space.index_type
        )
        data = np.zeros((self.space.size, len(self.target_atoms)), dtype=np.float64)

        for atom_index, value in self.target_atoms.items():
            input_indices = self.configurations ^ (1 << atom_index)
            indices[:, atom_index] = input_indices
            data[:, atom_index] = value

        op = csr_matrix((data.ravel(), indices.ravel(), indptr), shape=shape)

        return (self.amplitude, op)
    
    def emit_two_level_full_space_multi_atom_complex(self):
        shape = (self.space.size, self.space.size)
        indptr = np.zeros(self.space.size + 1, dtype=self.space.index_type)

        nnz_values = indptr[1:]
        for atom_index in self.target_atoms.keys():
            rydberg_states = (self.space.configurations >> atom_index) & 1 == 1
            input_indices = self.space.configurations[rydberg_states] ^ (1 << atom_index)
            nnz_values[input_indices] += 1

        np.cumsum(indptr, out=indptr)

        indices = np.zeros((indptr[-1],), dtype=self.space.index_type)
        data = np.zeros((indptr[-1],), dtype=np.complex128)

        index = indptr[0:-1]
        for atom_index, value in self.target_atoms.items():
            rydberg_states = (self.space.configurations >> atom_index) & 1 == 1
            input_indices = self.space.configurations[rydberg_states] ^ (1 << atom_index)

            nonzero_index = index[rydberg_states]
            indices[nonzero_index] = input_indices
            data[nonzero_index] = value
            index[input_indices] += 1

        op = csr_matrix((data, indices, indptr), shape=shape)
        op_H = csc_matrix((data.conj(), indices, indptr), shape=shape)
        return [
            (lambda t: self.amplitude(t) * np.exp(1j * self.phase(t)), op),
            (lambda t: self.amplitude(t) * np.exp(-1j * self.phase(t)), op_H),
        ]
    
    def emit_two_level_subspace_multi_atom_real(self):
        shape = (self.space.size, self.space.size)
        indptr = np.zeros(self.space.size + 1, dtype=self.space.index_type)

        nnz_values = indptr[1:]
        for atom_index, value in self.target_atoms.items():
            new_configurations = self.configurations ^ (1 << atom_index)
            input_indices = np.searchsorted(self.configurations, new_configurations)
            input_indices = input_indices[input_indices < self.configurations.size]

            indptr[input_indices] += 1

        np.cumsum(indptr, out=indptr)

        indices = np.zeros((indptr[-1],), dtype=self.space.index_type)
        data = np.zeros((indptr[-1],), dtype=np.float64)

        index = indptr[0:-1]
        for atom_index, value in self.target_atoms.items():
            new_configurations = self.configurations ^ (1 << atom_index)
            input_indices = np.searchsorted(self.configurations, new_configurations)

            input_indices = input_indices[input_indices < self.configurations.size]
            nonzero_index = index[input_indices]

            indices[nonzero_index] = input_indices
            data[nonzero_index] = value
            index[input_indices] += 1

        indptr[1:] = index
        indptr[0] = 0
        return csr_matrix((data, indices, indptr), shape=shape)

    def emit_two_level_subspace_multi_atom_complex(self):
        raise NotImplementedError("Complex valued multi-atom subspace not implemented.")

    def emit_two_level_full_space_single_atom(self):
        if self.phase is None:  # Real valued
            return self.emit_two_level_full_space_single_atom_real()
        else:  # Complex valued
            return self.emit_two_level_full_space_single_atom_complex()

    def emit_two_level_subspace_single_atom(self):
        if self.phase is None:
            return self.emit_two_level_subspace_single_atom_real()
        else:
            return self.emit_two_level_subspace_single_atom_complex()

    def emit_two_level_full_space_multi_atom(self):
        if self.phase is None:
            return self.emit_two_level_full_space_multi_atom_real()
        else:
            return self.emit_two_level_full_space_multi_atom_complex()
        
    def emit_two_level_subspace_multi_atom(self):
        if self.phase is None:
            return self.emit_two_level_subspace_multi_atom_real()
        else:
            return self.emit_two_level_subspace_multi_atom_complex()
        
    def emit_two_level_full_space(self):
        if len(self.target_atoms) == 1:
            return self.emit_two_level_full_space_single_atom()
        else:
            return self.emit_two_level_full_space_multi_atom()

    def emit_two_level_subspace(self):
        if len(self.target_atoms) == 1:
            return self.emit_two_level_subspace_single_atom()
        else:
            return self.emit_two_level_subspace_multi_atom()

    def emit(self, rabi_term: RabiTerm, level_coupling: LevelCoupling):
        self.target_atoms = rabi_term.target_atoms
        self.phase = rabi_term.phase
        self.amplitude = rabi_term.amplitude

        match (self.space):
            case (
                Space(SpaceType.FullSpace, LocalHilbertSpace.TwoLevel, _, _),
                rydberg,
            ):
                return self.emit_two_level_full_space()
            case (Space(SpaceType.SubSpace, LocalHilbertSpace.TwoLevel, _, _), rydberg):
                return self.emit_two_level_subspace()
            case (Space(_, LocalHilbertSpace.TwoLevel, _, _), hyperfine):
                raise ValueError("No hyperfine coupling for two-level space.")
            case _:
                raise NotImplementedError("Three-level space not implemented.")


def emit_rabi_terms(space: Space, term: RabiTerm) -> IndexMapping:
    configurations = space.configurations
    shape = (configurations.size, configurations.size)

    if space.space_type == SpaceType.FullSpace:
        match term:
            case RabiTerm(None, amplitude, dict([(int(atom_index), Real(value))])):
                (atom_index,) = target_atoms.keys()
                input_indices = configurations ^ (1 << atom_index)
                return [(lambda t: value * amplitude(t), IndexMapping(input_indices))]

            case RabiTerm(phase, amplitude, dict([(int(atom_index), Real(value))])):
                output_indices = (configurations >> atom_index) & 1 == 1
                input_indices = configurations[output_indices] ^ (1 << atom_index)
                op = IndexMapping(input_indices, output_indices)
                return [
                    (lambda t: value * amplitude(t) * np.exp(1j * phase(t)), op),
                    (
                        lambda t: value * amplitude(t) * np.exp(-1j * phase(t)),
                        op.ajoint(),
                    ),
                ]

            case RabiTerm(None, amplitude, dict(target_atoms)):
                indptr = np.zeros(space.size + 1, dtype=space.index_type)
                indptr[1:] = len(target_atoms)

                np.cumsum(indptr, out=indptr)

                indices = np.zeros(
                    (space.size, len(target_atoms)), dtype=space.index_type
                )
                data = np.zeros((space.size, len(target_atoms)), dtype=np.float64)

                for atom_index, value in target_atoms.items():
                    input_indices = configurations ^ (1 << atom_index)
                    indices[:, atom_index] = input_indices
                    data[:, atom_index] = value

                op = csr_matrix((data.ravel(), indices.ravel(), indptr), shape=shape)

                return (amplitude, op)

            case RabiTerm(phase, amplitude, dict(target_atoms)):
                indptr = np.zeros(space.size + 1, dtype=space.index_type)

                nnz_values = indptr[1:]
                for atom_index in target_atoms.keys():
                    rydberg_states = (configurations >> atom_index) & 1 == 1
                    input_indices = configurations[rydberg_states] ^ (1 << atom_index)
                    nnz_values[input_indices] += 1

                np.cumsum(indptr, out=indptr)

                indices = np.zeros((indptr[-1],), dtype=space.index_type)
                data = np.zeros((indptr[-1],), dtype=np.complex128)

                index = indptr[0:-1]
                for atom_index, value in target_atoms.items():
                    rydberg_states = (configurations >> atom_index) & 1 == 1
                    input_indices = configurations[rydberg_states] ^ (1 << atom_index)

                    nonzero_index = index[rydberg_states]
                    indices[nonzero_index] = input_indices
                    data[nonzero_index] = value
                    index[input_indices] += 1

                op = csr_matrix((data, indices, indptr), shape=shape)
                op_H = csc_matrix((data.conj(), indices, indptr), shape=shape)
                return [
                    (lambda t: amplitude(t) * np.exp(1j * phase(t)), op),
                    (lambda t: amplitude(t) * np.exp(-1j * phase(t)), op_H),
                ]

    else:
        match term:
            case RabiTerm(None, amplitude, dict([(int(atom_index), Real(value))])):
                new_configurations = configurations ^ (1 << atom_index)
                input_indices = np.searchsorted(configurations, new_configurations)

                output_indices = input_indices < configurations.size
                input_indices = input_indices[output_indices]
                return [
                    (
                        lambda t: value * amplitude(t),
                        IndexMapping(input_indices, output_indices),
                    )
                ]

            case RabiTerm(phase, amplitude, dict([(int(atom_index), Real(value))])):
                rydberg_states = (configurations >> atom_index) & 1 == 1
                new_configurations = configurations[rydberg_states] ^ (1 << atom_index)
                input_indices = np.searchsorted(configurations, new_configurations)

                nonzero_indices = input_indices < configurations.size
                output_indices = np.logical_and(rydberg_states, nonzero_indices)
                input_indices = input_indices[nonzero_indices]
                op = IndexMapping(input_indices, output_indices)
                return [
                    (lambda t: value * amplitude(t) * np.exp(1j * phase(t)), op),
                    (
                        lambda t: value * amplitude(t) * np.exp(-1j * phase(t)),
                        op.ajoint(),
                    ),
                ]

            case RabiTerm(None, amplitude, dict(target_atoms)):
                indptr = np.zeros(configurations.size, dtype=space.index_type)

                nnz_values = indptr[1:]
                for atom_index, value in target_atoms.items():
                    new_configurations = configurations ^ (1 << atom_index)
                    input_indices = np.searchsorted(configurations, new_configurations)
                    nnz_values[input_indices < configurations.size] += 1

                np.cumsum(indptr, out=indptr)

                indices = np.zeros((indptr[-1],), dtype=space.index_type)
                data = np.zeros((indptr[-1],), dtype=np.float64)

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
                op = csr_matrix((data, indices, indptr), shape=shape)

                return (amplitude, op)

            case RabiTerm(phase, amplitude, dict(target_atoms)):
                indptr = np.zeros(space.size + 1, dtype=space.index_type)

                nnz_values = indptr[1:]
                for atom_index in target_atoms.keys():
                    rydberg_states = (configurations >> atom_index) & 1 == 1
                    input_indices = configurations[rydberg_states] ^ (1 << atom_index)
                    nnz_values[input_indices] += 1

                np.cumsum(indptr, out=indptr)

                indices = np.zeros((indptr[-1],), dtype=space.index_type)
                data = np.zeros((indptr[-1],), dtype=np.complex128)

                index = indptr[0:-1]
                for atom_index, value in target_atoms.items():
                    rydberg_states = (configurations >> atom_index) & 1 == 1
                    input_indices = configurations[rydberg_states] ^ (1 << atom_index)

                    nonzero_index = index[rydberg_states]
                    indices[nonzero_index] = input_indices
                    data[nonzero_index] = value
                    index[input_indices] += 1

                op = csr_matrix((data, indices, indptr), shape=shape)
                op_H = csc_matrix((data.conj(), indices, indptr), shape=shape)
                return [
                    (lambda t: amplitude(t) * np.exp(1j * phase(t)), op),
                    (lambda t: amplitude(t) * np.exp(-1j * phase(t)), op_H),
                ]


# def emit_two_level_rabi_csr_matrix(info: RabiTerm) -> csr_matrix:
#     shape = (info.space.size, info.space.size)
#     dtype = get_dtype(info.target_atoms)
#     match info:
#         case RabiTerm(
#             op_type=RabiOperatorType.ComplexValued,
#             target_atoms=target_atoms,
#             space=Space(
#                 space_type=SpaceType.FullSpace,
#                 configurations=configurations,
#             ) as space,
#         ):
#             indptr = np.zeros(space.size + 1, dtype=space.index_type)

#             nnz_values = indptr[1:]
#             for atom_index in target_atoms.keys():
#                 rydberg_states = (configurations >> atom_index) & 1 == 1
#                 input_indices = configurations[rydberg_states] ^ (1 << atom_index)
#                 nnz_values[input_indices] += 1

#             np.cumsum(indptr, out=indptr)

#             indices = np.zeros((indptr[-1],), dtype=space.index_type)
#             data = np.zeros((indptr[-1],), dtype=dtype)

#             index = indptr[0:-1]
#             for atom_index, value in target_atoms.items():
#                 rydberg_states = (configurations >> atom_index) & 1 == 1
#                 input_indices = configurations[rydberg_states] ^ (1 << atom_index)

#                 nonzero_index = index[rydberg_states]
#                 indices[nonzero_index] = input_indices
#                 data[nonzero_index] = value
#                 index[input_indices] += 1

#             return csr_matrix((data, indices, indptr), shape=shape, dtype=dtype)

#         case RabiTerm(
#             op_type=RabiOperatorType.ComplexValued,
#             target_atoms=target_atoms,
#             space=Space(
#                 space_type=SpaceType.SubSpace,
#                 configurations=configurations,
#             ) as space,
#         ):
#             indptr = np.zeros(space.size + 1, dtype=space.index_type)

#             nnz_values = indptr[1:]
#             for atom_index, value in target_atoms.items():
#                 rydberg_states = (configurations >> atom_index) & 1 == 1

#                 new_configurations = configurations[rydberg_states] ^ (1 << atom_index)
#                 input_indices = np.searchsorted(configurations, new_configurations)
#                 input_indices = input_indices[input_indices < configurations.size]

#                 nnz_values[input_indices] += 1

#             np.cumsum(indptr, out=indptr)

#             indices = np.zeros((indptr[-1],), dtype=space.index_type)
#             data = np.zeros((indptr[-1],), dtype=dtype)

#             index = indptr[0:-1]
#             for atom_index, value in target_atoms.items():
#                 rydberg_states = (configurations >> atom_index) & 1 == 1

#                 new_configurations = configurations[rydberg_states] ^ (1 << atom_index)
#                 input_indices = np.searchsorted(configurations, new_configurations)

#                 input_indices = input_indices[input_indices < configurations.size]
#                 nonzero_index = index[input_indices]

#                 indices[nonzero_index] = input_indices
#                 data[nonzero_index] = value
#                 index[input_indices] += 1

#             indptr[1:] = index
#             indptr[0] = 0
#             return csr_matrix((data, indices, indptr), shape=shape, dtype=dtype)

#         case _:
#             raise RuntimeError(
#                 "Fatal compilation error when lowering Rabi term to python."
#             )


# def emit_rabi_matrix(info: RabiTerm) -> Union[csr_matrix, IndexMapping]:
#     match info:
#         case RabiTerm(
#             target_atoms=target_atoms,
#             space=Space(n_level=LocalHilbertSpace.TwoLevel),
#         ) if len(target_atoms) == 1:
#             return emit_two_level_rabi_index_map(info)
#         case RabiTerm(space=Space(n_level=LocalHilbertSpace.TwoLevel)):
#             return emit_two_level_rabi_csr_matrix(info)
#         case RabiTerm(
#             space=Space(n_level=LocalHilbertSpace.ThreeLevel),
#         ):
#             raise NotImplementedError
#         case _:
#             raise RuntimeError(
#                 "Fatal compilation error when lowering Rabi term to python."
#             )


def emit_detuning_matrix(info: DetuningTerm):
    match info:
        case DetuningTerm(
            target_atoms=target_atoms,
            level_coupling=hyperfine,
            space=Space(n_level=n_level, configurations=configurations),
        ):
            diagonal = np.zeros(configurations.size, dtype=np.float64)
            for atom_index, detuning_value in target_atoms.items():
                mask = is_hyperfine_state(configurations, atom_index, n_level)
                diagonal[mask] += detuning_value

            return Diagonal(diagonal)

        case DetuningTerm(
            target_atoms=target_atoms,
            level_coupling=rydberg,
            space=Space(n_level=n_level, configurations=configurations),
        ):
            diagonal = np.zeros(configurations.size, dtype=np.float64)
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
