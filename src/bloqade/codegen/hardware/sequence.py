from pydantic.dataclasses import dataclass
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

    def scan(self, ast: SequenceExpr):
        match ast:
            case Sequence(value):
                self.level_coupling = LevelCoupling.Rydberg
                if self.level_coupling in value:
                    self.rydberg = PulseCodeGen.emit(self, value[self.level_coupling])

            case NamedSequence(sub_sequence, _):
                self.scan(sub_sequence)

            case _:
                # TODO: Inprove error message.
                raise ValueError()

    def emit(self, ast: SequenceExpr):
        self.scan(ast)
        return EffectiveHamiltonian(rydberg=self.rydberg)
