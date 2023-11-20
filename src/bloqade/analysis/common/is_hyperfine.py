from beartype.typing import Any
import bloqade.ir.control.sequence as sequence
from bloqade.ir.visitor import BloqadeIRVisitor


class IsHyperfineSequence(BloqadeIRVisitor):
    def __init__(self):
        self.is_hyperfine = False

    def generic_visit(self, node: Any) -> Any:
        # skip visiting children if we already know there are hyperfine pulses
        if self.is_hyperfine:
            return

        super().generic_visit(node)

    def visit_sequence_Sequence(self, node: sequence.Sequence) -> Any:
        self.is_hyperfine = self.is_hyperfine or sequence.hyperfine in node.pulses

    def emit(self, node) -> bool:
        self.visit(node)
        return self.is_hyperfine
