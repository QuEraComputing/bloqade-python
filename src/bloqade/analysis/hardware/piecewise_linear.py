from functools import cached_property
import bloqade.ir.control.waveform as waveform
import bloqade.ir.scalar as scalar
from bloqade.ir.control.waveform import PythonFn
from bloqade.ir.visitor.waveform import WaveformVisitor

from pydantic.dataclasses import dataclass
from decimal import Decimal
from beartype.typing import Any, Union


@dataclass(frozen=True)
class PiecewiseLinearResult:
    start_expr: Union[waveform.Waveform, scalar.Scalar]
    stop_expr: Union[waveform.Waveform, scalar.Scalar]
    duration_expr: scalar.Scalar

    @cached_property
    def start(self):
        if isinstance(self.start_expr, waveform.Waveform):
            return self.start_expr.eval_decimal(Decimal(0))
        else:
            return self.start_expr()

    @cached_property
    def stop(self):
        if isinstance(self.stop_expr, waveform.Waveform):
            return self.stop_expr.eval_decimal(self.stop_expr.duration())
        else:
            return self.stop_expr()

    @cached_property
    def duration(self):
        return self.duration_expr()


class PiecewiseLinearValidator(WaveformVisitor):
    def __init__(self):
        self.result = None

    def check(self, start_expr, stop_expr, duration_expr):
        if self.result is None:
            self.result = PiecewiseLinearResult(
                start_expr=start_expr,
                stop_expr=stop_expr,
                duration_expr=duration_expr,
            )

        else:
            other = PiecewiseLinearResult(
                start_expr=start_expr,
                stop_expr=stop_expr,
                duration_expr=duration_expr,
            )

            if self.result.stop != other.start:
                time_str = str(self.result.duration_expr).replace("\n", "\n    ")
                left_str = str(self.result.stop_expr).replace("\n", "\n    ")
                right_str = str(other.start_expr).replace("\n", "\n    ")
                raise ValueError(
                    "failed to compile waveform to piecewise linear. "
                    f"found discontinuity at time={self.result.duration}\n"
                    f"with left value {self.result.stop_value} "
                    f"and right value {self.result.start_value}:\n"
                    f"time expression:\n    {time_str}\n"
                    f"left expression:\n    {left_str}\n"
                    f"right expression:\n    {right_str} \n"
                )

            self.result = PiecewiseLinearResult(
                start_expr=self.result.start_expr,
                stop_expr=other.stop_expr,
                duration_expr=self.result.duration_expr + other.duration_expr,
            )

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
        duration = ast.waveform.duration()
        value = ast.waveform.eval_decimal(
            duration,
        )
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
        PiecewiseLinearValidator().scan(ast.waveform)
        # make sure slice is is piecewise linear
        self.check(ast, ast, ast.duration)

    def visit_add(self, ast: waveform.Add):
        scanner = PiecewiseLinearValidator()
        scanner.scan(ast.left)
        scanner.scan(ast.right)

        self.check(ast, ast, ast.duration)

    def visit_negative(self, ast: waveform.Negative):
        self.visit(ast.waveform)

    def visit_scale(self, ast: waveform.Scale):
        self.visit(ast.waveform)

    def scan(self, ast: waveform.Waveform) -> PiecewiseLinearResult:
        self.result = None
        self.visit(ast)
        return self.result
