from pydantic.dataclasses import dataclass
from bloqade.ir.pulse import PulseExpr
from bloqade.ir.sequence import SequenceExpr, Sequence, NamedSequence, LevelCoupling
from bloqade.codegen.hardware.pulse import PulseCodeGen
from quera_ahs_utils.quera_ir.task_specification import (
    EffectiveHamiltonian,
    RydbergHamiltonian,
)
from typing import Optional


@dataclass
class SequenceCodeGen(PulseCodeGen):
    rydberg: Optional[RydbergHamiltonian] = None

    def assignment_scan(self, ast: PulseExpr):
        match ast:
            case Sequence(value):
                self.level_coupling = LevelCoupling.Rydberg
                if self.level_coupling in value:
                    self.rydberg = PulseCodeGen(
                        self.n_atoms,
                        self.assignments,
                        level_coupling=self.level_coupling,
                    ).assignment_scan(self, value[self.level_coupling])

            case NamedSequence(sub_sequence, _):
                self.assignment_scan(sub_sequence)

            case _:
                # TODO: Inprove error message.
                raise ValueError()

    def scan(self, ast: SequenceExpr):
        match ast:
            case Sequence(value):
                self.level_coupling = LevelCoupling.Rydberg
                if self.level_coupling in value:
                    self.rydberg = PulseCodeGen(
                        self.n_atoms,
                        self.assignments,
                        level_coupling=self.level_coupling,
                    ).emit(self, value[self.level_coupling])

            case NamedSequence(sub_sequence, _):
                self.scan(sub_sequence)

            case _:
                # TODO: Inprove error message.
                raise ValueError()

    def emit(self, ast: SequenceExpr):
        self.assignment_scan(ast)
        self.scan(ast)
        return EffectiveHamiltonian(rydberg=self.rydberg)
