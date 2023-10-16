# The goal of this transformation is to make it so that
# every sequence either has either just a Rydberg or Hyperfine
# drive or both with the same duration. This is done by
# slicing the longer sequence to match the shorter one.
# and then appending the remaining drive to the end of the
# sequence.

from bloqade.ir import scalar
from bloqade.ir.visitor.analog_circuit import AnalogCircuitVisitor
import bloqade.ir.control.sequence as sequence
from bloqade.builder.typing import LiteralType
from beartype.typing import Any, Dict
from beartype import beartype


class NormalizeSequences(AnalogCircuitVisitor):
    def __init__(self, assignments: Dict[str, LiteralType]) -> None:
        self.assignments = assignments
        self.rydberg_pulses = []
        self.hyperfine_pulses = []

    def visit_sequence(self, ast: sequence.Sequence):
        if len(ast.pulses) == 1:
            self.sequences.append(ast)
        elif len(ast.pulses) == 2:
            rydberg_pulse = ast.pulses[sequence.rydberg]
            hyperfine_pulse = ast.pulses[sequence.hyperfine]

            duration = scalar.symbolic_min(
                rydberg_pulse.duration, hyperfine_pulse.duration
            )

            self.sequences.append(ast[:duration])
            self.sequences.append(ast[duration:])

    def visit_named_sequence(self, ast: sequence.NamedSequence) -> Any:
        self.visit(ast.sequence)

    def visit_append_sequence(self, ast: sequence.Append) -> Any:
        for sub_sequence in ast.sequences:
            self.visit(sub_sequence)

    def visit_slice_sequence(self, ast: sequence.Slice) -> Any:
        new_sequence = NormalizeSequences(self.assignments).emit(ast.sequence)

        self.sequences.append(new_sequence[ast.interval.start : ast.interval.stop])

    @beartype
    def emit(self, ast: sequence.SequenceExpr) -> sequence.SequenceExpr:
        self.visit(ast)

        if len(self.sequences) > 1:
            return sequence.Append(self.sequences)
        else:
            return ast
