import bloqade.ir.control.waveform as waveform
import bloqade.ir.control.field as field
import bloqade.ir.control.pulse as pulse
import bloqade.ir.control.sequence as sequence
import bloqade.ir.analog_circuit as analog_circuit 
from bloqade.ir.visitor.waveform import WaveformVisitor
from bloqade.ir.visitor.analog_circuit import AnalogCircuitVisitor
from decimal import Decimal
from beartype.typing import Any, Dict
from beartype import beartype
from pydantic.dataclasses import dataclasss


@dataclasss(frozen=True)
class IsConstantWaveformResult:
    is_constant: bool
    effective_waveform: waveform.Constant


class IsConstantWaveform(WaveformVisitor):
    @beartype
    def __init__(self, assignments: Dict[str, Decimal]) -> None:
        self.assignments = dict(assignments)
        self.is_constant = True

    def visit_constant(self, _: waveform.Constant) -> Any:
        pass

    def visit_linear(self, ast: waveform.Linear) -> Any:
        diff = ast.stop(**self.assignments) - ast.start(**self.assignments)
        self.is_constant = self.is_constant and (diff == 0)

    def visit_poly(self, ast: waveform.Poly) -> Any:
        coeffs = [coeff(**self.assignments) for coeff in ast.coeffs]
        if any(coeff != 0 for coeff in coeffs[1:]):
            self.is_constant = False

    def visit_python_fn(self, ast: waveform.PythonFn) -> Any:
        # can't analyze python functions, assume it's not constant
        self.is_constant = False

    def visit_add(self, ast: waveform.Add) -> Any:
        self.visit(ast.left)
        self.visit(ast.right)

    def visit_alligned(self, ast: waveform.AlignedWaveform) -> Any:
        self.visit(ast.waveform)

    def visit_negative(self, ast: waveform.Negative) -> Any:
        self.visit(ast.waveform)

    def visit_record(self, ast: waveform.Record) -> Any:
        self.visit(ast.waveform)

    def visit_sample(self, ast: waveform.Sample) -> Any:
        self.visit(ast.waveform)

    def visit_scale(self, ast: waveform.Scale) -> Any:
        self.visit(ast.waveform)

    def visit_slice(self, ast: waveform.Slice) -> Any:
        self.visit(ast.waveform)

    def visit_smooth(self, ast: waveform.Smooth) -> Any:
        self.visit(ast.waveform)

    def visit_append(self, ast: waveform.Append) -> Any:
        value = None
        for waveform in ast.waveforms:
            result = IsConstantWaveform(self.assignments).emit(waveform)
            if value is None:
                value = result.effective_waveform.value

            self.is_constant = (self.is_constant and result.is_constant) and (
                result.effective_waveform.value == value
            )

    def emit(self, ast: waveform.Waveform) -> IsConstantWaveformResult:
        self.visit(ast)
        duration = ast.duration(**self.assignments)
        value = ast.eval_decimal(duration, **self.assignments)

        wf = waveform.Constant(value, duration)

        return IsConstantWaveformResult(self.is_constant, wf)
