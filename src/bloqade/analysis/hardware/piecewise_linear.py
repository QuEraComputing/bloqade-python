from functools import cached_property
import bloqade.ir.control.waveform as waveform
import bloqade.ir.scalar as scalar
from bloqade.ir.control.waveform import PythonFn
from bloqade.ir.visitor import BloqadeIRVisitor

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


class PiecewiseLinearValidator(BloqadeIRVisitor):
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
                    f"with left value {self.result.stop} "
                    f"and right value {self.result.start}:\n"
                    f"time expression:\n    {time_str}\n"
                    f"left expression:\n    {left_str}\n"
                    f"right expression:\n    {right_str} \n"
                )

            self.result = PiecewiseLinearResult(
                start_expr=self.result.start_expr,
                stop_expr=other.stop_expr,
                duration_expr=self.result.duration_expr + other.duration_expr,
            )

    def visit_waveform_Constant(self, ast: waveform.Constant) -> Any:
        self.check(ast.value, ast.value, ast.duration)

    def visit_waveform_Linear(self, ast: waveform.Linear) -> Any:
        self.check(ast.start, ast.stop, ast.duration)

    def visit_waveform_Poly(self, ast: waveform.Poly) -> Any:
        if len(ast.coeffs) == 0:  # zero
            start_expr = scalar.Literal(0)
            stop_expr = scalar.Literal(0)
            duration_expr = ast.duration
        elif len(ast.coeffs) == 1:  # non-zero constant
            start_expr = ast.coeffs[0]
            stop_expr = ast.coeffs[0]
            duration_expr = ast.duration
        elif len(ast.coeffs) == 2:  # linear
            duration_expr = ast.duration
            start_expr = ast.coeffs[0]
            stop_expr = ast.coeffs[0] + ast.coeffs[1] * duration_expr
        else:
            raise ValueError(
                "failed to compile waveform to piecewise linear. "
                f"found polynomial of degree > 1:\n {ast!s}"
            )

        self.check(start_expr, stop_expr, duration_expr)

    def visit_waveform_Sample(self, ast: waveform.Sample) -> Any:
        if ast.interpolation != waveform.Interpolation.Linear:
            raise ValueError(
                "failed to compile waveform to piecewise linear. "
                f"found non-linear interpolation:\n '{ast.interpolation!s}'"
            )

        self.check(ast, ast, ast.duration)

    def visit_waveform_PythonFn(self, ast: PythonFn) -> Any:
        raise ValueError(
            "PythonFn Waveforms cannot be compiled to piecewise linear. "
            "Try using the `sample` method to sample the waveform and "
            "interpolate it linearly."
        )

    def visit_waveform_Slice(self, ast: waveform.Slice):
        # make sure waveform being sliced is piecewise linear
        PiecewiseLinearValidator().scan(ast.waveform)
        # make sure slice is is piecewise linear
        self.check(ast, ast, ast.duration)

    def visit_waveform_Add(self, ast: waveform.Add):
        scanner = PiecewiseLinearValidator()
        left_result = scanner.scan(ast.left)
        right_result = scanner.scan(ast.right)

        if left_result.duration != right_result.duration:
            raise ValueError(
                "failed to compile waveform to piecewise linear. "
                f"found mismatched durations in the sum of two waveforms:\n"
                f"left duration: {left_result.duration}\n"
                f"right duration: {right_result.duration}\n"
            )

        self.check(ast, ast, ast.duration)

    def visit_waveform_Smooth(self, ast: waveform.Smooth) -> Any:
        raise ValueError(
            "failed to compile waveform to piecewise linear. "
            f"found Smooth waveform:\n {ast!s}"
        )

    def scan(self, ast: waveform.Waveform) -> PiecewiseLinearResult:
        self.result = None
        self.visit(ast)
        return self.result
