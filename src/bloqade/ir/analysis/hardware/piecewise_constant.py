from typing import Any
import bloqade.ir.control.waveform as waveform
from bloqade.ir.visitor.waveform import WaveformVisitor
from bloqade.ir.analysis.common.scan_variables import ScanVariablesWaveform
from bloqade.ir.analysis.common.is_constant import IsConstantWaveform


class PiecewiseConstantValidator(WaveformVisitor):
    def __init__(self, assignments) -> None:
        self.assignments = dict(assignments)

    def emit_leaf_error(self, ast: waveform.Waveform):
        expr_msg = str(ast).replace("\n", "\n    ")
        var_result = ScanVariablesWaveform().emit(ast)

        assigment_str = "\n    ".join(
            [f"{k} -> {self.assignments[k]}" for k in var_result]
        )

        raise Exception(
            f"failed to compile to piecewise constant, "
            f"found Non-constant segment in waveform:\n    {expr_msg}\n"
            + (f"with assignments:\n    {assigment_str}" if assigment_str else "")
        )

    def visit_constant(self, ast: waveform.Constant) -> Any:
        pass

    def visit_linear(self, ast: waveform.Linear) -> Any:
        if ast.start(**self.assignments) != self.stop(**self.assignments):
            self.emit_leaf_error(ast)

    def visit_poly(self, ast: waveform.Poly) -> Any:
        if len(ast.coeffs) > 1:
            self.emit_leaf_error(ast)

    def visit_python_fn(self, ast: waveform.PythonFn) -> Any:
        self.emit_leaf_error(ast)

    def visit_add(self, ast: waveform.Add) -> Any:
        self.visit(ast.left)
        self.visit(ast.right)

    def visit_alligned(self, ast: waveform.AlignedWaveform) -> Any:
        self.visit(ast.waveform)

    def visit_append(self, ast: waveform.Append) -> Any:
        for wf in ast.waveforms:
            self.visit(wf)

    def visit_negative(self, ast: waveform.Negative) -> Any:
        self.visit(ast.waveform)

    def visit_scale(self, ast: waveform.Scale) -> Any:
        self.visit(ast.waveform)

    def visit_sample(self, ast: waveform.Sample) -> Any:
        if ast.interpolation != waveform.Interpolation.Constant:
            raise ValueError(
                "failed to compile waveform to piecewise linear. "
                f"found non-linear interpolation:\n '{ast.interpolation!s}'"
            )

    def visit_record(self, ast: waveform.Record):
        duration = ast.duration(**self.assignments)
        self.assignments[ast.var.name] = ast.waveform.eval_decimal(
            duration, **self.assignments
        )
        self.visit(ast.waveform)

    def visit_slice(self, ast: waveform.Slice) -> Any:
        self.visit(ast.waveform)

    def visit_smooth(self, ast: waveform.Smooth) -> Any:
        res = IsConstantWaveform(self.assignments).emit(ast.waveform)

        if res.is_constant:
            pass
        else:
            raise ValueError(
                "failed to compile waveform to piecewise constant. "
                "found Smooth waveform"
            )

    def scan(self, ast: waveform.Waveform) -> None:
        self.visit(ast)
