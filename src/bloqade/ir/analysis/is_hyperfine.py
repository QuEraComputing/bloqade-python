from typing import Any
import bloqade.ir.analog_circuit as analog_circuit
import bloqade.ir.control.sequence as sequence
from bloqade.ir.visitor.analog_circuit import AnalogCircuitVisitor


class IsHyperfineSequence(AnalogCircuitVisitor):
    def __init__(self):
        self.is_hyperfine = False

    def visit_analog_circuit(self, ast: analog_circuit.AnalogCircuit) -> Any:
        self.visit(ast.sequence)

    def visit_append_sequence(self, ast: sequence.Append) -> Any:
        list(map(self.visit, ast.sequences))

    def visit_slice_sequence(self, ast: sequence.Slice) -> Any:
        self.visit(ast.sequence)

    def visit_named_sequence(self, ast: sequence.NamedSequence) -> Any:
        self.visit(ast.sequence)

    def visit_sequence(self, ast: sequence.Sequence) -> Any:
        self.is_hyperfine = self.is_hyperfine or sequence.hyperfine in ast.pulses

    def emit(self, ast: analog_circuit.AnalogCircuit) -> bool:
        self.visit(ast)
        return self.is_hyperfine
