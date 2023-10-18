import bloqade.ir.control.waveform as waveform
import bloqade.ir.scalar as scalar
from bloqade.ir.control.waveform import PythonFn
from bloqade.ir.visitor.waveform import WaveformVisitor
from bloqade.ir.analysis.common.scan_variables import ScanVariablesWaveform
from bloqade.builder.typing import LiteralType

from decimal import Decimal
from pydantic.dataclasses import dataclass
from typing import Any, Dict, Union


@dataclass(init=False)
class PiecewiseLinearValidatorResults:
    assignments: Dict[str, LiteralType]
    start_expr: Union[waveform.Waveform, scalar.Scalar]
    stop_expr: Union[waveform.Waveform, scalar.Scalar]
    time: scalar.Scalar
    
    def eval_stop_expr(self, expr: Union[waveform.Waveform, scalar.Scalar]):
        if isinstance(expr, waveform.Waveform):
            duration = expr.duration(**self.assignments)
            return expr.eval_decimal(duration, **self.assignments)
        else:
            return expr(**self.assignments)

    def eval_start_expr(self, expr: Union[waveform.Waveform, scalar.Scalar]):
        if isinstance(expr, waveform.Waveform):
            return expr.eval_decimal(Decimal("0"), **self.assignments)
        else:
            return expr(**self.assignments)

    def check_continuity(self, other: "PiecewiseLinearValidatorResults"):

        start_value = self.eval_start_expr(other.start_expr)
        stop_value = self.eval_stop_expr(self.stop_expr)

        if start_value != stop_value:
            var_result = ScanVariablesWaveform().emit(self.stop_expr)
            var_result = var_result.union(ScanVariablesWaveform().emit(other.start_expr))
            var_result = var_result.union(ScanVariablesWaveform().emit(self.time))

            assignments = "\n    ".join(
                [f"{k} -> {self.assignments.get(k, 'Not Defined')}" for k in var_result]
            )
            time_str = str(self.time).replace("\n", "\n    ")
            left_str = str(self.stop_expr).replace("\n", "\n    ")
            right_str = str(other.start_expr).replace("\n", "\n    ")
            raise ValueError(
                "failed to compile waveform to piecewise linear. "
                f"found discontinuity at time={self.time(**self.assignments)}\n"
                f"with left value {self.stop_value} "
                f"and right value {start_value}:\n"
                f"time expression:\n    {time_str}\n"
                f"left expression:\n    {left_str}\n"
                f"right expression:\n    {right_str} \n"
                f"with assignments:\n    {assignments}"
            )


class PiecewiseLinearValidator(WaveformVisitor):
    def __init__(self, assignments: Dict[str, LiteralType] = {}):
        self.assignments = dict(assignments)
        self.result = None

    def check(self, start_expr, stop_expr, duration_expr):
        if self.result is None:
            self.result = PiecewiseLinearValidatorResults(
                assignments=self.assignments,
                start_expr=start_expr,
                stop_expr=stop_expr,
                time=duration_expr,
            )
        else:
            new_result = PiecewiseLinearValidatorResults(
                assignments=self.assignments,
                start_expr=start_expr,
                stop_expr=stop_expr,
                time=self.result.time + duration_expr,
            )
            self.result.check_continuity(new_result)
            self.result = new_result

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

    def scan(self, ast: waveform.Waveform) -> PiecewiseLinearValidatorResults:
        self.visit(ast)

        return self.result
