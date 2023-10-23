import bloqade.ir.control.waveform as waveform
import bloqade.ir.scalar as scalar
from bloqade.ir.control.waveform import PythonFn
from bloqade.ir.visitor.waveform import WaveformVisitor
from bloqade.analysis.common.scan_variables import ScanVariablesWaveform
from bloqade.builder.typing import LiteralType

from decimal import Decimal
from typing import Any, Dict


class PiecewiseLinearValidator(WaveformVisitor):
    def __init__(self, assignments: Dict[str, LiteralType] = {}):
        self.assignments = dict(assignments)
        self.start_expr = None
        self.stop_expr = None
        self.duration_expr = None

    def eval_start_value(self, expr):
        if isinstance(expr, waveform.Waveform):
            return expr.eval_decimal(Decimal(0), **self.assignments)
        else:
            return expr(**self.assignments)

    def eval_stop_value(self, expr):
        if isinstance(expr, waveform.Waveform):
            return expr.eval_decimal(
                expr.duration(**self.assignments), **self.assignments
            )
        else:
            return expr(**self.assignments)

    def check(self, start_expr, stop_expr, duration_expr):
        if self.start_expr is None:
            self.start_expr = start_expr
            self.stop_expr = stop_expr
            self.duration_expr = duration_expr

        else:
            stop_value = self.eval_stop_value(self.stop_expr)
            start_value = self.eval_start_value(start_expr)
            time_value = self.duration_expr(**self.assignments)

            if start_value != stop_value:
                var_result = ScanVariablesWaveform().emit(self.stop_expr)
                var_result = var_result.union(ScanVariablesWaveform().emit(start_expr))
                var_result = var_result.union(
                    ScanVariablesWaveform().emit(self.duration_expr)
                )

                assignments = "\n    ".join(
                    [
                        f"{k} -> {self.assignments.get(k, 'Not Defined')}"
                        for k in var_result
                    ]
                )
                time_str = str(self.time_expr).replace("\n", "\n    ")
                left_str = str(self.stop_expr).replace("\n", "\n    ")
                right_str = str(start_expr).replace("\n", "\n    ")
                raise ValueError(
                    "failed to compile waveform to piecewise linear. "
                    f"found discontinuity at time={time_value}\n"
                    f"with left value {self.result.stop_value} "
                    f"and right value {self.result.start_value}:\n"
                    f"time expression:\n    {time_str}\n"
                    f"left expression:\n    {left_str}\n"
                    f"right expression:\n    {right_str} \n"
                    f"with assignments:\n    {assignments}"
                )

            self.stop_expr = stop_expr
            self.duration_expr = self.duration_expr + duration_expr

    def visit_constant(self, ast: waveform.Constant) -> Any:
        self.check(ast.value, ast.value, ast.duration)

    def visit_linear(self, ast: waveform.Linear) -> Any:
        self.check(ast.start, ast.stop, ast.duration)

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

        self.check(start_expr, stop_expr, duration_expr)

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
        self.check(ast, ast, ast.duration)

    def visit_python_fn(self, ast: PythonFn) -> Any:
        raise ValueError(
            "PythonFn Waveforms cannot be compiled to piecewise linear. "
            "Try using the `sample` method to sample the waveform and "
            "interpolate it linearly."
        )

    def visit_alligned(self, ast: waveform.AlignedWaveform) -> Any:
        self.visit(ast.waveform)

    def visit_append(self, ast: waveform.Append):
        for wf in ast.waveforms:
            self.visit(wf)

    def visit_slice(self, ast: waveform.Slice):
        # make sure waveform being sliced is piecewise linear
        PiecewiseLinearValidator(self.assignments).scan(ast.waveform)
        # make sure slice is is piecewise linear
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

    def scan(self, ast: waveform.Waveform):
        self.start_expr = None
        self.stop_expr = None
        self.duration_expr = None

        self.visit(ast)
