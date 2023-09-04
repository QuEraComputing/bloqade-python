from bloqade.constants import RB_C6
from bloqade.ir.control.sequence import (
    RydbergLevelCoupling,
    HyperfineLevelCoupling,
)
from bloqade.emulate.ir.emulator import (
    DetuningOperatorData,
    EmulatorProgram,
    Geometry,
    LaserCoupling,
    DetuningTerm,
    RabiOperatorData,
    RabiOperatorType,
    RabiTerm,
    Visitor,
)
from bloqade.emulate.ir.space import (
    Space,
    ThreeLevelAtomType,
    TwoLevelAtomType,
)
from bloqade.emulate.ir.state_vector import (
    RabiOperator,
    DetuningOperator,
    RydbergHamiltonian,
)
from bloqade.emulate.sparse_operator import IndexMapping
from scipy.sparse import csr_matrix
import numpy as np
from numpy.typing import NDArray
from typing import Dict, Tuple, Union
from dataclasses import dataclass, field

OperatorData = Union[DetuningOperatorData, RabiOperatorData]
MatrixTypes = Union[csr_matrix, IndexMapping, NDArray]


@dataclass
class CompileCache:
    """This class is used to cache the results of the code generation."""

    operator_cache: Dict[Tuple[Geometry, OperatorData], MatrixTypes] = field(
        default_factory=dict
    )
    space_cache: Dict[Geometry, Tuple[Space, NDArray]] = field(default_factory=dict)


class RydbergHamiltonianCodeGen(Visitor):
    def __init__(self, compile_cache: CompileCache = CompileCache()):
        self.rabi_ops = []
        self.detuning_ops = []
        self.level_coupling = None
        self.level_couplings = set()
        self.compile_cache = compile_cache

    def visit_emulator_program(self, emulator_program: EmulatorProgram):
        self.level_couplings = set(list(emulator_program.drives.keys()))

        self.visit(emulator_program.geometry)
        for level_coupling, laser_coupling in emulator_program.drives.items():
            self.level_coupling = level_coupling
            self.visit(laser_coupling)

    def visit_geometry(self, geometry: Geometry):
        self.geometry = geometry

        if geometry in self.compile_cache.space_cache:
            self.space, self.rydberg = self.compile_cache.space_cache[geometry]
            return

        self.space = Space.create(geometry)
        positions = geometry.positions

        # generate rydberg interaction elements
        self.rydberg = np.zeros(self.space.size, dtype=np.float64)

        for index_1, pos_1 in enumerate(positions):
            pos_1 = np.asarray(list(map(float, pos_1)))
            is_rydberg_1 = self.space.is_rydberg_at(index_1)
            for index_2, pos_2 in enumerate(positions[index_1 + 1 :], index_1 + 1):
                pos_2 = np.asarray(list(map(float, pos_2)))
                distance = np.linalg.norm(pos_1 - pos_2)

                rydberg_interaction = RB_C6 / (distance**6)

                if rydberg_interaction <= np.finfo(np.float64).eps:
                    continue

                mask = np.logical_and(is_rydberg_1, self.space.is_rydberg_at(index_2))
                self.rydberg[mask] += rydberg_interaction

        self.compile_cache.space_cache[geometry] = (self.space, self.rydberg)

    def visit_laser_coupling(self, laser_coupling: LaserCoupling):
        terms = laser_coupling.detuning + laser_coupling.rabi
        for term in terms:
            self.visit(term)

    def visit_detuning_operator_data(self, detuning_data: DetuningOperatorData):
        if (self.geometry, detuning_data) in self.compile_cache.operator_cache:
            return self.compile_cache.operator_cache[(self.space, detuning_data)]

        diagonal = np.zeros(self.space.size, dtype=np.float64)

        match (self.space.geometry.atom_type, self.level_coupling):
            case (TwoLevelAtomType(), RydbergLevelCoupling()):
                state = TwoLevelAtomType.State.Rydberg
            case (ThreeLevelAtomType(), RydbergLevelCoupling()):
                state = ThreeLevelAtomType.State.Rydberg
            case (ThreeLevelAtomType(), HyperfineLevelCoupling()):
                state = ThreeLevelAtomType.State.Hyperfine

        for atom_index, value in detuning_data.target_atoms.items():
            diagonal[self.space.is_state_at(atom_index, state)] += float(value)

        self.compile_cache.operator_cache[(self.geometry, detuning_data)] = diagonal
        return diagonal

    def visit_rabi_operator_data(self, rabi_operator_data: RabiOperatorData):
        if (self.geometry, rabi_operator_data) in self.compile_cache.operator_cache:
            return self.compile_cache.operator_cache[
                (self.geometry, rabi_operator_data)
            ]

        # Get the from and to states for term
        match (self.space.geometry.atom_type, self.level_coupling):
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
        if rabi_operator_data.operator_type is RabiOperatorType.RabiSymmetric:

            def matrix_ele(atom_index):
                return self.space.swap_state_at(atom_index, fro, to)

        elif rabi_operator_data.operator_type is RabiOperatorType.RabiAsymmetric:

            def matrix_ele(atom_index):
                return self.space.transition_state_at(atom_index, fro, to)

        # generate rabi operator
        if len(rabi_operator_data.target_atoms) == 1:
            ((atom_index, value),) = rabi_operator_data.target_atoms.items()
            operator = matrix_ele(atom_index) * value
        else:
            indptr = np.zeros(self.space.size + 1, dtype=self.space.index_type)

            for atom_index in rabi_operator_data.target_atoms:
                row_indices, col_indices = matrix_ele(atom_index)
                indptr[1:][row_indices] += 1
            np.cumsum(indptr, out=indptr)

            indices = np.zeros(indptr[-1], dtype=self.space.index_type)
            data = np.zeros(indptr[-1], dtype=np.float64)

            for atom_index, value in rabi_operator_data.target_atoms.items():
                row_indices, col_indices = matrix_ele(atom_index)
                indices[indptr[:-1][row_indices]] = col_indices
                data[indptr[:-1][row_indices]] = value
                indptr[:-1][row_indices] += 1

            indptr[1:] = indptr[:-1]
            indptr[0] = 0

            operator = csr_matrix(
                (data, indices, indptr),
                shape=(self.space.size, self.space.size),
            )

        self.compile_cache.operator_cache[
            (self.geometry, rabi_operator_data)
        ] = operator
        return operator

    def visit_detuning_term(self, detuning_term: DetuningTerm):
        self.detuning_ops.append(
            DetuningOperator(
                diagonal=self.visit(detuning_term.operator_data),
                amplitude=detuning_term.amplitude,
            )
        )

    def visit_rabi_term(self, rabi_term: RabiTerm):
        self.rabi_ops.append(
            RabiOperator(
                op=self.visit(rabi_term.operator_data),
                amplitude=rabi_term.amplitude,
                phase=rabi_term.phase,
            )
        )

    def emit(
        self, emulator_program: EmulatorProgram
    ) -> Tuple[RydbergHamiltonian, CompileCache]:
        self.visit(emulator_program)
        hamiltonian = RydbergHamiltonian(
            emulator_ir=emulator_program,
            space=self.space,
            rydberg=self.rydberg,
            detuning_ops=self.detuning_ops,
            rabi_ops=self.rabi_ops,
        )
        return hamiltonian, self.compile_cache
