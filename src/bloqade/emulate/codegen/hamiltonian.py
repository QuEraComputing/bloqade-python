from bloqade.constants import RB_C6
from bloqade.emulate.ir.emulator import (
    DetuningOperatorData,
    EmulatorProgram,
    LevelCoupling,
    Register,
    Fields,
    DetuningTerm,
    RabiOperatorData,
    RabiOperatorType,
    RabiTerm,
    Visitor,
)
from bloqade.emulate.ir.space import Space
from bloqade.emulate.ir.atom_type import (
    TwoLevelAtomType,
    ThreeLevelAtomType,
)
from bloqade.emulate.ir.state_vector import (
    RabiOperator,
    DetuningOperator,
    RydbergHamiltonian,
)
from bloqade.emulate.sparse_operator import (
    IndexMapping,
    SparseMatrixCSR,
)
from scipy.sparse import csr_matrix
import numpy as np
from numpy.typing import NDArray
from typing import Dict, Optional, Tuple, Union
from dataclasses import dataclass, field

OperatorData = Union[DetuningOperatorData, RabiOperatorData]
MatrixTypes = Union[csr_matrix, IndexMapping, NDArray]


@dataclass
class CompileCache:
    """This class is used to cache the results of the code generation."""

    operator_cache: Dict[Tuple[Register, OperatorData], MatrixTypes] = field(
        default_factory=dict
    )
    space_cache: Dict[Register, Tuple[Space, NDArray]] = field(default_factory=dict)


class RydbergHamiltonianCodeGen(Visitor):
    def __init__(self, compile_cache: Optional[CompileCache] = None):
        if compile_cache is None:
            compile_cache = CompileCache()

        self.rabi_ops = []
        self.detuning_ops = []
        self.level_coupling = None
        self.level_couplings = set()
        self.compile_cache = compile_cache

    def visit_emulator_program(self, emulator_program: EmulatorProgram):
        self.level_couplings = set(list(emulator_program.pulses.keys()))

        self.visit(emulator_program.register)
        for level_coupling, laser_coupling in emulator_program.pulses.items():
            self.level_coupling = level_coupling
            self.visit(laser_coupling)

    def visit_register(self, register: Register):
        self.register = register

        if register in self.compile_cache.space_cache:
            self.space, self.rydberg = self.compile_cache.space_cache[register]
            return

        self.space = Space.create(register)
        sites = register.sites

        # generate rydberg interaction elements
        self.rydberg = np.zeros(self.space.size, dtype=np.float64)

        for index_1, site_1 in enumerate(sites):
            site_1 = np.asarray(list(map(float, site_1)))
            is_rydberg_1 = self.space.is_rydberg_at(index_1)
            for index_2, sites_2 in enumerate(sites[index_1 + 1 :], index_1 + 1):
                sites_2 = np.asarray(list(map(float, sites_2)))
                distance = np.linalg.norm(site_1 - sites_2)

                rydberg_interaction = RB_C6 / (distance**6)

                if rydberg_interaction <= np.finfo(np.float64).eps:
                    continue

                mask = np.logical_and(is_rydberg_1, self.space.is_rydberg_at(index_2))
                self.rydberg[mask] += rydberg_interaction

        self.compile_cache.space_cache[register] = (self.space, self.rydberg)

    def visit_fields(self, fields: Fields):
        terms = fields.detuning + fields.rabi
        for term in terms:
            self.visit(term)

    def visit_detuning_operator_data(self, detuning_data: DetuningOperatorData):
        if (self.register, detuning_data) in self.compile_cache.operator_cache:
            return self.compile_cache.operator_cache[(self.register, detuning_data)]

        diagonal = np.zeros(self.space.size, dtype=np.float64)
        if self.space.atom_type == TwoLevelAtomType():
            state = TwoLevelAtomType.State.Rydberg
        elif self.space.atom_type == ThreeLevelAtomType():
            if self.level_coupling is LevelCoupling.Rydberg:
                state = ThreeLevelAtomType.State.Rydberg
            elif self.level_coupling is LevelCoupling.Hyperfine:
                state = ThreeLevelAtomType.State.Hyperfine

        for atom_index, value in detuning_data.target_atoms.items():
            diagonal[self.space.is_state_at(atom_index, state)] -= float(value)

        self.compile_cache.operator_cache[(self.register, detuning_data)] = diagonal
        return diagonal

    def visit_rabi_operator_data(self, rabi_operator_data: RabiOperatorData):
        if (self.register, rabi_operator_data) in self.compile_cache.operator_cache:
            return self.compile_cache.operator_cache[
                (self.register, rabi_operator_data)
            ]

        # get the form `to` and `from` states for the rabi term
        if self.space.atom_type == TwoLevelAtomType():
            to = TwoLevelAtomType.State.Ground
            fro = TwoLevelAtomType.State.Rydberg

        elif self.space.atom_type == ThreeLevelAtomType():
            if self.level_coupling is LevelCoupling.Rydberg:
                to = ThreeLevelAtomType.State.Hyperfine
                fro = ThreeLevelAtomType.State.Rydberg
            elif self.level_coupling == LevelCoupling.Hyperfine:
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
            ((atom_index, _),) = rabi_operator_data.target_atoms.items()
            operator = IndexMapping(self.space.size, *matrix_ele(atom_index))
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

            operator = SparseMatrixCSR.create(
                (data, indices, indptr),
                shape=(self.space.size, self.space.size),
            )
            # operator = csr_matrix(
            #     (data, indices, indptr),
            #     shape=(self.space.size, self.space.size),
            # )

        self.compile_cache.operator_cache[
            (self.register, rabi_operator_data)
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

    def emit(self, emulator_program: EmulatorProgram) -> RydbergHamiltonian:
        self.visit(emulator_program)
        hamiltonian = RydbergHamiltonian(
            emulator_ir=emulator_program,
            space=self.space,
            rydberg=self.rydberg,
            detuning_ops=self.detuning_ops,
            rabi_ops=self.rabi_ops,
        )
        return hamiltonian
