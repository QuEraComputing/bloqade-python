from bloqade.constants import RB_C6
from bloqade.ir.control.sequence import (
    LevelCoupling,
    RydbergLevelCoupling,
    HyperfineLevelCoupling,
)
from bloqade.emulator.ir.emulator_program import (
    EmulatorProgram,
    LaserCoupling,
    DetuningTerm,
    RabiTerm,
    Visitor,
)
from bloqade.emulator.ir.space import (
    Space,
    SpaceType,
    LocalHilbertSpace,
    TwoLevelState,
    ThreeLevelState,
    is_state,
)
from bloqade.emulator.sparse_operator import IndexMapping, Diagonal
from scipy.sparse import csr_matrix, csc_matrix
import numpy as np


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
        input_indices = self.space.configurations[output_indices] ^ (1 << atom_index)

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
            input_indices = self.space.configurations[rydberg_states] ^ (
                1 << atom_index
            )
            nnz_values[input_indices] += 1

        np.cumsum(indptr, out=indptr)

        indices = np.zeros((indptr[-1],), dtype=self.space.index_type)
        data = np.zeros((indptr[-1],), dtype=np.complex128)

        index = indptr[0:-1]
        for atom_index, value in self.target_atoms.items():
            rydberg_states = (self.space.configurations >> atom_index) & 1 == 1
            input_indices = self.space.configurations[rydberg_states] ^ (
                1 << atom_index
            )

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

    def emit_two_level_subspace_single_atom_real(self):
        ((atom_index, value),) = self.target_atoms.items()

        new_configurations = self.space.configurations ^ (1 << atom_index)
        input_indices = np.searchsorted(self.space.configurations, new_configurations)

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
        input_indices = np.searchsorted(self.space.configurations, new_configurations)

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

    def emit_two_level_subspace_multi_atom_real(self):
        shape = (self.space.size, self.space.size)
        indptr = np.zeros(self.space.size + 1, dtype=self.space.index_type)

        nnz_values = indptr[1:]
        for atom_index, value in self.target_atoms.items():
            new_configurations = self.configurations ^ (1 << atom_index)
            input_indices = np.searchsorted(self.configurations, new_configurations)
            input_indices = input_indices[input_indices < self.configurations.size]

            nnz_values[input_indices] += 1

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
        shape = (self.space.size, self.space.size)
        indptr = np.zeros(self.space.size + 1, dtype=self.space.index_type)

        nnz_values = indptr[1:]
        for atom_index, value in self.target_atoms.items():
            rydberg_states = (self.configurations >> atom_index) & 1 == 1

            new_configurations = self.configurations[rydberg_states] ^ (1 << atom_index)
            input_indices = np.searchsorted(self.configurations, new_configurations)
            input_indices = input_indices[input_indices < self.configurations.size]

            nnz_values[input_indices] += 1

        np.cumsum(indptr, out=indptr)

        indices = np.zeros((indptr[-1],), dtype=self.space.index_type)
        data = np.zeros((indptr[-1],), dtype=np.float64)

        index = indptr[0:-1]
        for atom_index, value in self.target_atoms.items():
            rydberg_states = (self.configurations >> atom_index) & 1 == 1

            new_configurations = self.configurations[rydberg_states] ^ (1 << atom_index)
            input_indices = np.searchsorted(self.configurations, new_configurations)

            input_indices = input_indices[input_indices < self.configurations.size]
            nonzero_index = index[input_indices]

            indices[nonzero_index] = input_indices
            data[nonzero_index] = value
            index[input_indices] += 1

        indptr[1:] = index
        indptr[0] = 0

        op = csr_matrix((data, indices, indptr), shape=shape)
        op_H = csc_matrix((data.conj(), indices, indptr), shape=shape)
        return [
            (lambda t: self.amplitude(t) * np.exp(1j * self.phase(t)), op),
            (lambda t: self.amplitude(t) * np.exp(-1j * self.phase(t)), op_H),
        ]

    def emit_two_level_subspace(self):
        match (self.target_atoms, self.phase):
            case (dict([(_, _)]), None):
                self.emit_two_level_subspace_single_atom_real()
            case (dict([(_, _)]), _):
                self.emit_two_level_subspace_single_atom_complex()
            case (_, None):
                self.emit_two_level_subspace_multi_atom_real()
            case (_, _):
                self.emit_two_level_subspace_multi_atom_complex()

    def emit_two_level_full_space(self):
        match (self.target_atoms, self.phase):
            case (dict([(_, _)]), None):
                self.emit_two_level_full_space_single_atom_real()
            case (dict([(_, _)]), _):
                self.emit_two_level_full_space_single_atom_complex()
            case (_, None):
                self.emit_two_level_full_space_multi_atom_real()
            case (_, _):
                self.emit_two_level_full_space_multi_atom_complex()

    def emit(self, rabi_term: RabiTerm, level_coupling: LevelCoupling):
        self.target_atoms = rabi_term.target_atoms
        self.phase = rabi_term.phase
        self.amplitude = rabi_term.amplitude

        match (self.space):
            case (
                Space(SpaceType.FullSpace, LocalHilbertSpace.TwoLevel, _, _),
                RydbergLevelCoupling(),
            ):
                return self.emit_two_level_full_space()
            case (
                Space(SpaceType.SubSpace, LocalHilbertSpace.TwoLevel, _, _),
                HyperfineLevelCoupling(),
            ):
                return self.emit_two_level_subspace()
            case (Space(_, LocalHilbertSpace.TwoLevel, _, _), HyperfineLevelCoupling()):
                raise ValueError("No hyperfine coupling for two-level space.")
            case _:
                raise NotImplementedError("Three-level space not implemented.")


class LowerToAnalogGate(Visitor):
    def __init__(self):
        self.terms = []
        self.space = None
        self.n_level = None
        self.level_coupling = None
        self.rydberg_state = None

    def visit_emulator_program(self, emulator_program: EmulatorProgram):
        self.visit(emulator_program.space)

        if emulator_program.rydberg is not None:
            self.visit(emulator_program.rydberg)

        if emulator_program.hyperfine is not None:
            self.visit(emulator_program.hyperfine)

    def visit_space(self, space: Space):
        self.space = space
        self.n_level = space.n_level

        if space.n_level == LocalHilbertSpace.TwoLevel:
            self.rydberg_state = TwoLevelState.rydberg
        elif space.n_level == LocalHilbertSpace.ThreeLevel:
            self.rydberg_state = ThreeLevelState.rydberg

        configurations = space.configurations
        atom_coordinates = space.atom_coordinates

        # generate rydberg interaction matrix
        diagonal = np.zeros(configurations.size, dtype=np.float64)

        for index_1, coordinate_1 in enumerate(atom_coordinates):
            coordinate_1 = np.asarray(coordinate_1)
            is_rydberg_1 = is_state(configurations, index_1, self.rydberg_state)
            for index_2, coordinate_2 in enumerate(
                atom_coordinates[index_1 + 1 :], index_1 + 1
            ):
                coordinate_2 = np.asarray(coordinate_2)
                distance = np.linalg.norm(coordinate_1 - coordinate_2)

                rydberg_interaction = RB_C6 / (distance**6)

                if rydberg_interaction <= np.finfo(np.float64).eps:
                    continue

                mask = np.logical_and(
                    is_rydberg_1,
                    is_state(configurations, index_2, self.rydberg_state),
                )
                diagonal[mask] += rydberg_interaction

        self.terms.append((None, Diagonal(diagonal)))

    def visit_laser_coupling(self, laser_coupling: LaserCoupling):
        self.level_coupling = laser_coupling.level_coupling
        terms = laser_coupling.detuning + laser_coupling.rabi
        for term in terms:
            self.visit(term)

    def visit_detuning_term(self, detuning_term: DetuningTerm):
        target_atoms = detuning_term.target_atoms
        configurations = self.space.configurations

        diagonal = np.zeros(configurations.size, dtype=np.float64)
        for atom_index, detuning_value in target_atoms.items():
            mask = is_state(configurations, atom_index, self.rydberg_state)
            diagonal[mask] += detuning_value

        detuning_op = Diagonal(diagonal)

        self.terms.append((detuning_term.amplitude, detuning_op))

    def visit_rabi_term(self, rabi_term: RabiTerm):
        self.terms += self.lower_rabi_term.emit(rabi_term, self.level_coupling)

    def emit(self, emulator_program: EmulatorProgram):
        from bloqade.emulator.ir.state_vector import AnalogGate

        self.lower_rabi_term = LowerRabiTerm(emulator_program.space)

        self.visit(emulator_program)

        return AnalogGate(
            terms=self.terms,
            final_time=emulator_program.duration,
            initial_time=0.0,
        )
