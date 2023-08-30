from bloqade.constants import RB_C6
from bloqade.ir.control.sequence import (
    RydbergLevelCoupling,
    HyperfineLevelCoupling,
)
from bloqade.emulate.ir.emulator import (
    EmulatorProgram,
    LaserCoupling,
    DetuningTerm,
    RabiTerm,
    Visitor,
)
from bloqade.emulate.ir.space import (
    Space,
    TwoLevelAtomType,
    ThreeLevelAtomType,
)
from bloqade.emulate.ir.state_vector import (
    RabiOperator,
    DetuningOperator,
    RydbergHamiltonian,
)
from bloqade.emulate.sparse_operator import IndexMapping
from scipy.sparse import csr_matrix
import numpy as np


class RydbergHamiltonianCodeGen(Visitor):
    def __init__(self):
        self.rabi_ops = []
        self.detuning_ops = []
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
        self.n_level = space.atom_type.n_level
        atom_coordinates = space.atom_coordinates

        # generate rydberg interaction elements
        self.rydberg = np.zeros(space.size, dtype=np.float64)

        for index_1, coordinate_1 in enumerate(atom_coordinates):
            coordinate_1 = np.asarray(coordinate_1)
            is_rydberg_1 = space.is_rydberg_at(index_1)
            for index_2, coordinate_2 in enumerate(
                atom_coordinates[index_1 + 1 :], index_1 + 1
            ):
                coordinate_2 = np.asarray(coordinate_2)
                distance = np.linalg.norm(coordinate_1 - coordinate_2)

                rydberg_interaction = RB_C6 / (distance**6)

                if rydberg_interaction <= np.finfo(np.float64).eps:
                    continue

                mask = np.logical_and(is_rydberg_1, space.is_rydberg_at(index_2))
                self.rydberg[mask] += rydberg_interaction

    def visit_laser_coupling(self, laser_coupling: LaserCoupling):
        self.level_coupling = laser_coupling.level_coupling
        terms = laser_coupling.detuning + laser_coupling.rabi
        for term in terms:
            self.visit(term)

    def visit_detuning_term(self, detuning_term: DetuningTerm):
        diagonal = np.zeros(self.space.size, dtype=np.float64)

        match (self.space.atom_type, self.level_coupling):
            case (TwoLevelAtomType(), RydbergLevelCoupling()):
                state = TwoLevelAtomType.State.Rydberg
            case (ThreeLevelAtomType(), RydbergLevelCoupling()):
                state = ThreeLevelAtomType.State.Rydberg
            case (ThreeLevelAtomType(), HyperfineLevelCoupling()):
                state = ThreeLevelAtomType.State.Hyperfine

        for atom_index, value in enumerate(detuning_term.target_atoms):
            diagonal[self.space.is_state_at(atom_index, state)] = value

        self.detuning_ops.append(
            DetuningOperator(
                diagonal=diagonal,
                amplitude=detuning_term.amplitude,
            )
        )

    def visit_rabi_term(self, rabi_term: RabiTerm):
        # Get the from and to states for term
        match (self.space.atom_type, self.level_coupling):
            case (TwoLevelAtomType(), RydbergLevelCoupling()):
                to = TwoLevelAtomType.State.Ground
                fro = TwoLevelAtomType.State.Rydberg
            case (ThreeLevelAtomType(), RydbergLevelCoupling()):
                to = ThreeLevelAtomType.State.Hyperfine
                fro = ThreeLevelAtomType.State.Rydberg
            case (ThreeLevelAtomType(), HyperfineLevelCoupling()):
                to = ThreeLevelAtomType.State.Ground
                fro = ThreeLevelAtomType.State.Hyperfine

        # get matrix element generating function
        if rabi_term.phase is None:
            # matrix_ele = lambda atom_index: self.space.swap_state_at(
            #     atom_index, fro, to
            # )
            def matrix_ele(atom_index):
                return self.space.swap_state_at(atom_index, fro, to)

        else:

            def matrix_ele(atom_index):
                return self.space.swap_state_at(atom_index, fro, to, rabi_term.phase)

            # matrix_ele = lambda atom_index: self.space.transition_state_at(
            #     atom_index, fro, to
            # )

        # generate rabi operator
        if len(rabi_term.target_atoms) == 1:
            ((atom_index, value),) = rabi_term.target_atoms.items()
            self.rabi_ops.append(
                RabiOperator(
                    op=IndexMapping(self.space.size, *matrix_ele(atom_index)),
                    amplitude=rabi_term.amplitude,
                    phase=rabi_term.phase,
                )
            )
        else:
            indptr = np.zeros(self.space.size + 1, dtype=self.space.index_type)

            for atom_index in rabi_term.target_atoms:
                row_indices, col_indices = matrix_ele(atom_index)
                indptr[1:][row_indices] = 1
            np.cumsum(indptr, out=indptr)

            indices = np.zeros(indptr[-1], dtype=self.space.index_type)
            data = np.zeros(indptr[-1], dtype=np.float64)

            for atom_index, value in rabi_term.target_atoms.items():
                row_indices, col_indices = matrix_ele(atom_index)
                indices[indptr[1:][row_indices]] = col_indices
                data[indptr[1:][row_indices]] = value

            self.rabi_ops.append(
                RabiOperator(
                    op=csr_matrix(
                        (data, indices, indptr),
                        shape=(self.space.size, self.space.size),
                    ),
                    amplitude=rabi_term.amplitude,
                    phase=rabi_term.phase,
                )
            )

    def emit(self, emulator_program: EmulatorProgram) -> RydbergHamiltonian:
        self.visit(emulator_program)
        return RydbergHamiltonian(
            rydberg=self.rydberg,
            detuning_ops=self.detuning_ops,
            rabi_ops=self.rabi_ops,
        )
