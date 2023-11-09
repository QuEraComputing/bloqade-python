from bloqade.constants import RB_C6
from bloqade.emulate.ir.emulator import (
    DetuningOperatorData,
    EmulatorProgram,
    LevelCoupling,
    Register,
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
import numpy as np
from beartype.typing import Tuple, Union, FrozenSet
from dataclasses import dataclass

OperatorData = Union[DetuningOperatorData, RabiOperatorData]


@dataclass(frozen=True)
class RydbergHamiltonianScanResults:
    detuning_terms: FrozenSet[Tuple[int, LevelCoupling]]
    rabi_terms: FrozenSet[Tuple[int, LevelCoupling]]


class RydbergHamiltonianScan(Visitor):
    def __init__(self):
        self.detuning_terms = set()
        self.rabi_terms = set()

    def visit_emulator_program(self, emulator_program: EmulatorProgram):
        for detuning_term in emulator_program.detuning_terms:
            self.visit(detuning_term)

        for rabi_term in emulator_program.rabi_terms:
            self.visit(rabi_term)

    def visit_detuning_operator_data(self, op_data: DetuningOperatorData):
        self.detuning_terms = self.detuning_terms.union(
            *[(op_data.level_coupling, idx) for idx in op_data.target_atoms.keys()]
        )

    def visit_rabi_operator_data(self, op_data: RabiOperatorData):
        self.rabi_terms = self.rabi_terms.union(
            *[(op_data.level_coupling, idx) for idx in op_data.target_atoms.keys()]
        )

    def visit_detuning_term(self, detuning_term: DetuningTerm):
        self.visit(detuning_term.operator_data)

    def visit_rabi_term(self, rabi_term: RabiTerm):
        self.visit(rabi_term.operator_data)

    def scan(self, emulator_program: EmulatorProgram) -> RydbergHamiltonianScanResults:
        self.visit(emulator_program)

        return RydbergHamiltonianScanResults(
            frozenset(self.detuning_terms),
            frozenset(self.rabi_terms),
        )


class RydbergHamiltonianCodeGen(Visitor):
    def __init__(self, scan_results: RydbergHamiltonianScanResults):
        self.scan_results = scan_results
        self.detuning_masks = None
        self.rabi_row_indices = None
        self.rabi_col_indices = None
        self.col_index_detuning = {}
        self.col_index_rabi = {}
        self.completed_detuning_masks = set()
        self.completed_rabi_terms = set()

    def visit_emulator_program(self, emulator_program: EmulatorProgram):
        self.visit(emulator_program.register)

        n_detuning_diagonals = len(self.scan_results.detuning_diagonals)
        n_rabi_indices = len(self.scan_results.rabi_terms)

        sorted_detuning_terms = sorted(list(self.scan_results.detuning_terms))
        sorted_rabi_terms = sorted(list(self.scan_results.rabi_terms))

        for index, detuning_term in enumerate(sorted_detuning_terms):
            self.col_index_detuning[detuning_term] = index

        for index, rabi_term in enumerate(sorted_rabi_terms):
            self.col_index_rabi[rabi_term] = index

        self.detuning_masks = np.zeros(
            (self.space.size, n_detuning_diagonals), dtype=bool
        )
        self.rabi_col_indices = [None for _ in range(n_rabi_indices)]
        self.rabi_row_indices = [None for _ in range(n_rabi_indices)]

        list(map(self.visit, emulator_program.detuning_terms))
        list(map(self.visit, emulator_program.rabi_terms))

    def visit_register(self, register: Register):
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

    def visit_detuning_operator_data(self, op_data: DetuningOperatorData):
        if self.space.atom_type == TwoLevelAtomType():
            state = TwoLevelAtomType.State.Rydberg
        elif self.space.atom_type == ThreeLevelAtomType():
            if self.level_coupling is LevelCoupling.Rydberg:
                state = ThreeLevelAtomType.State.Rydberg
            elif self.level_coupling is LevelCoupling.Hyperfine:
                state = ThreeLevelAtomType.State.Hyperfine

        for atom_index in op_data.target_atoms.keys():
            detuning_term = (op_data.level_coupling, atom_index)
            if detuning_term in self.completed_detuning_masks:
                continue

            col_index = self.col_index_detuning[detuning_term]
            self.detuning_masks = self.detuning_masks.at[:, col_index].set(
                self.space.is_state_at(atom_index, state)
            )

            self.completed_detuning_masks.add(detuning_term)

    def visit_rabi_operator_data(self, op_data: RabiOperatorData):
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
        if op_data.operator_type is RabiOperatorType.RabiSymmetric:

            def matrix_ele(atom_index):
                return self.space.swap_state_at(atom_index, fro, to)

        elif op_data.operator_type is RabiOperatorType.RabiAsymmetric:

            def matrix_ele(atom_index):
                return self.space.transition_state_at(atom_index, fro, to)

        for atom_index in op_data.target_atoms.keys():
            rabi_term = (op_data.level_coupling, atom_index)
            if rabi_term in self.completed_rabi_terms:
                continue

            row_indices, col_indices = matrix_ele(atom_index)

            col_index = self.col_index_rabi[rabi_term]
            self.rabi_col_indices[col_index] = col_indices
            self.rabi_row_indices[col_index] = row_indices

            self.completed_rabi_terms.add(rabi_term)

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
