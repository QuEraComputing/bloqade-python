import bloqade.ir.control.waveform as waveform
from bloqade.ir.control.waveform import Record
from bloqade.ir.visitor.waveform import WaveformVisitor

from typing import Dict, Tuple, List, Union
from pydantic.dataclasses import dataclass
from bisect import bisect_left, bisect_right
import numbers
from decimal import Decimal


@dataclass(frozen=True)
class PiecewiseLinear:
    times: List[Decimal]
    values: List[Decimal]

    def eval(self, time: Decimal) -> Decimal:
        if time >= self.times[-1]:
            return self.values[-1]

        elif time <= self.times[0]:
            return self.values[0]
        else:
            index = bisect_right(self.times, time) - 1

            m = (self.values[index + 1] - self.values[index])(
                self.times[index + 1] - self.times[index]
            )
            t = time - self.times[index]
            b = self.values[index]

            return m * t + b

    def slice(self, start_time: Decimal, stop_time: Decimal) -> "PiecewiseLinear":
        if start_time == stop_time:
            return [Decimal(0.0), Decimal(0.0)], [Decimal(0.0), Decimal(0.0)]

        start_index = bisect_right(self.times, start_time)
        stop_index = bisect_left(self.times, stop_time)
        start_value = self.eval(start_time)
        stop_value = self.eval(stop_time)

        absolute_times = [start_time] + self.times[start_index:stop_index] + [stop_time]
        values = [start_value] + self.values[start_index:stop_index] + [stop_value]

        return PiecewiseLinear([time - start_time for time in absolute_times], values)

    def append(self, other: "PiecewiseLinear"):
        assert self.values[-1] == other.values[0]

        return PiecewiseLinear(
            times=self.times + [time + self.times[-1] for time in other.times[1:]],
            values=self.values + other.values[1:],
        )


def check_continiuity(left, right):
    if left != right:
        diff = abs(left - right)
        raise ValueError(
            f"discontinuity with a jump of {diff} found when compiling to "
            "piecewise linear."
        )


class PiecewiseLinearCodeGen(WaveformVisitor):
    def __init__(self, assignments: Dict[str, Union[numbers.Real, List[numbers.Real]]]):
        self.assignments = assignments
        self.times = []
        self.values = []

    def append_timeseries(self, start, stop, duration):
        if len(self.times) == 0:
            self.times = [Decimal(0), duration]
            self.values = [start, stop]
        else:
            check_continiuity(self.values[-1], start)

            self.times.append(duration + self.times[-1])
            self.values.append(stop)

    def visit_linear(self, ast: waveform.Linear) -> Tuple[List[Decimal], List[Decimal]]:
        duration = ast.duration(**self.assignments)
        start = ast.start(**self.assignments)
        stop = ast.stop(**self.assignments)
        self.append_timeseries(start, stop, duration)

    def visit_constant(
        self, ast: waveform.Constant
    ) -> Tuple[List[Decimal], List[Decimal]]:
        duration = ast.duration(**self.assignments)
        value = ast.value(**self.assignments)
        self.append_timeseries(value, value, duration)

    def visit_poly(self, ast: waveform.Poly) -> Tuple[List[Decimal], List[Decimal]]:
        order = len(ast.coeffs) - 1
        duration = ast.duration(**self.assignments)

        if len(ast.coeffs) == 0:
            start = Decimal(0)
            stop = Decimal(0)
        elif len(ast.coeffs) == 1:
            start = ast.coeffs[0](**self.assignments)
            stop = start
        elif len(ast.coeffs) == 2:
            duration = ast.duration(**self.assignments)
            start = ast.coeffs[0](**self.assignments)
            stop = start + ast.coeffs[1](**self.assignments) * duration
        else:
            raise ValueError(
                "Failed to compile Waveform to piecewise linear,"
                f"found Polynomial of order {order}."
            )

        self.append_timeseries(start, stop, duration)

    def visit_negative(
        self, ast: waveform.Negative
    ) -> Tuple[List[Decimal], List[Decimal]]:
        self.visit(ast.waveform)
        self.values = [-value for value in self.values]

    def visit_scale(self, ast: waveform.Scale) -> Tuple[List[Decimal], List[Decimal]]:
        self.visit(ast.waveform)
        scaler = ast.scalar(**self.assignments)
        self.values = [scaler * value for value in self.values]

    def visit_slice(self, ast: waveform.Slice) -> Tuple[List[Decimal], List[Decimal]]:
        duration = ast.waveform.duration(**self.assignments)
        if ast.interval.start is None:
            start_time = Decimal(0)
        else:
            start_time = ast.interval.start(**self.assignments)

        if ast.interval.stop is None:
            stop_time = duration
        else:
            stop_time = ast.interval.stop(**self.assignments)

        if start_time < 0:
            raise ValueError((f"start time for slice {start_time} is smaller than 0."))

        if stop_time > duration:
            raise ValueError(
                (f"end time for slice {stop_time} is larger than duration {duration}.")
            )

        if stop_time < start_time:
            raise ValueError(
                (
                    f"end time for slice {stop_time} is smaller than "
                    f"starting value for slice {start_time}."
                )
            )

        pwl = PiecewiseLinearCodeGen(self.assignments).emit(ast.waveform)
        new_pwl = pwl.slice(start_time, stop_time)

        self.times = new_pwl.times
        self.values = new_pwl.values

    def visit_append(self, ast: waveform.Append) -> Tuple[List[Decimal], List[Decimal]]:
        pwl = PiecewiseLinearCodeGen(self.assignments).emit(ast.waveforms[0])

        for sub_expr in ast.waveforms[1:]:
            new_pwl = PiecewiseLinearCodeGen(self.assignments).emit(sub_expr)

            # skip instructions with duration=0
            if new_pwl.times[-1] == Decimal(0):
                continue

            check_continiuity(pwl.values[-1], new_pwl.values[0])
            pwl = pwl.append(new_pwl)

        self.times = pwl.times
        self.values = pwl.values

    def visit_sample(self, ast: waveform.Sample) -> Tuple[List[Decimal], List[Decimal]]:
        if ast.interpolation is not waveform.Interpolation.Linear:
            raise ValueError(
                "Failed to compile waveform to piecewise linear, "
                f"found piecewise {ast.interpolation.value} interpolation."
            )

        self.times, self.values = ast.samples(**self.assignments)

    def visit_record(self, ast: Record) -> Tuple[List[Decimal], List[Decimal]]:
        self.visit(ast.waveform)

    def emit(self, ast: waveform.Waveform) -> PiecewiseLinear:
        self.visit(ast)
        return PiecewiseLinear(self.times, self.values)
