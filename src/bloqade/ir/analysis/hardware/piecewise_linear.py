import bloqade.ir.control.waveform as waveform
import bloqade.ir.scalar as scalar
from bloqade.ir.control.waveform import PythonFn
from bloqade.ir.visitor.waveform import WaveformVisitor
from bloqade.ir.analysis.common.scan_variables import ScanVariablesWaveform
from bloqade.builder.typing import LiteralType

from decimal import Decimal
from pydantic.dataclasses import dataclass
from typing import Any, Dict, Union


@dataclass
class PiecewiseLinearValidatorResults:
    start_expr: Union[waveform.Waveform, scalar.Scalar]
    stop_expr: Union[waveform.Waveform, scalar.Scalar]
    duration_expr: scalar.Scalar
    stop_value: Decimal
    start_value: Decimal
    duration: Decimal
    time: Decimal


class PiecewiseLinearValidator(WaveformVisitor):
    def __init__(self, assignments: Dict[str, LiteralType] = {}):
        self.assignments = dict(assignments)
        self.start_expr = None
        self.stop_expr = None
        self.duration_expr = None
        self.time = Decimal(0)

    def check_continuity(self, start_expr, stop_expr, duration_expr):
        if self.start_expr is None:
            self.start_expr = start_expr
            self.stop_expr = stop_expr
            self.duration_expr = duration_expr
            duration = duration_expr(**self.assignments)
            if isinstance(start_expr, waveform.Waveform):
                self.start_value = start_expr.eval_decimal(
                    Decimal("0"), **self.assignments
                )
            else:
                self.start_value = start_expr(**self.assignments)

            if isinstance(stop_expr, waveform.Waveform):
                self.stop_value = stop_expr.eval_decimal(duration, **self.assignments)
            else:
                self.stop_value = stop_expr(**self.assignments)

            self.time = duration
            return

        duration = duration_expr(**self.assignments)

        if isinstance(start_expr, waveform.Waveform):
            start_value = start_expr.eval_decimal(duration, **self.assignments)
        else:
            start_value = start_expr(**self.assignments)

        if isinstance(stop_expr, waveform.Waveform):
            stop_value = stop_expr.eval_decimal(duration, **self.assignments)
        else:
            stop_value = stop_expr(**self.assignments)

        if start_value != self.stop_value:
            var_result = ScanVariablesWaveform().emit(self.stop_expr)
            var_result = var_result.union(ScanVariablesWaveform().emit(start_expr))

            assignments = "\n    ".join(
                [f"{k} -> {self.assignments[k]}" for k in var_result]
            )
            left_str = "\n    ".join(str(self.stop_expr).split("\n"))
            right_Str = "\n    ".join(str(start_expr).split("\n"))
            raise ValueError(
                "failed to compile waveform to piecewise linear. "
                f"found discontinuity at time={self.time}\n"
                f"with left value {self.stop_value} "
                f"and right value {start_value}:\n"
                f"left expression:\n    {left_str}\n"
                f"right expression:\n    {right_Str} \n"
                f"with assignments:\n    {assignments}"
            )

        self.start_expr = start_expr
        self.start_value = start_value
        self.stop_expr = stop_expr
        self.stop_value = stop_value
        self.time += duration_expr

    def visit_constant(self, ast: waveform.Constant) -> Any:
        self.check_continuity(ast.value, ast.value, ast.duration)

    def visit_linear(self, ast: waveform.Linear) -> Any:
        self.check_continuity(ast.start, ast.stop, ast.duration)

    def visit_poly(self, ast: waveform.Poly) -> Any:
        if len(ast.coeffs) == 0:
            start_expr = scalar.Literal(0)
            stop_expr = scalar.Literal(0)
            duration_expr = ast.duration
        elif len(ast.coeffs) == 1:
            start_expr = ast.coeffs[0]
            stop_expr = ast.coeffs[0]
            duration_expr = ast.duration
        elif len(ast.coeffs) == 2:
            duration_expr = ast.duration
            start_expr = ast.coeffs[0]
            stop_expr = ast.coeffs[0] + ast.coeffs[1] * duration_expr
        else:
            raise ValueError(
                "failed to compile waveform to piecewise linear. "
                f"found polynomial of degree > 1:\n {ast!s}"
            )

        self.check_continuity(start_expr, stop_expr, duration_expr)

    def visit_record(self, ast: waveform.Record):
        duration = ast.waveform.duration(**self.assignments)
        value = ast.waveform.eval_decimal(duration, **self.assignments)
        self.assignments[ast.var.name] = value
        self.visit(ast.waveform)

    def visit_sample(self, ast: waveform.Sample) -> Any:
        if ast.interpolation != waveform.Interpolation.Linear:
            raise ValueError(
                "failed to compile waveform to piecewise linear. "
                f"found non-linear interpolation:\n '{ast.interpolation!s}'"
            )
        self.check_continuity(ast, ast, ast.duration)

    def visit_python_fn(self, ast: PythonFn) -> Any:
        self.check_continuity(ast, ast, ast.duration)

    def visit_alligned(self, ast: waveform.AlignedWaveform) -> Any:
        self.visit(ast.waveform)

    def visit_append(self, ast: waveform.Append):
        for wf in ast.waveforms:
            self.visit(wf)

    def visit_slice(self, ast: waveform.Slice):
        PiecewiseLinearValidator(self.assignments).scan(ast.waveform)
        self.check_continuity(ast, ast, ast.duration)

    def visit_add(self, ast: waveform.Add):
        self.visit(ast.left)
        self.visit(ast.right)

    def visit_negative(self, ast: waveform.Negative):
        self.visit(ast.waveform)

    def visit_scale(self, ast: waveform.Scale):
        self.visit(ast.waveform)

    def visit_smooth(self, ast: waveform.Smooth):
        raise ValueError("Smoothed Waveforms cannot be compiled to piecewise linear.")

    def scan(self, ast: waveform.Waveform) -> PiecewiseLinearValidatorResults:
        self.visit(ast)
