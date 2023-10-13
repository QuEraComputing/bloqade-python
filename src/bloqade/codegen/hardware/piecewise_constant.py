import bloqade.ir.control.waveform as waveform
from bloqade.ir.visitor.waveform import WaveformVisitor

from typing import Dict, Tuple, List, Union
from pydantic.dataclasses import dataclass
from bisect import bisect_left
import numbers
from decimal import Decimal


@dataclass(frozen=True)
class PiecewiseConstant:
    times: List[Decimal]
    values: List[Decimal]

    def eval(self, time):
        if time >= self.times[-1]:
            return self.values[-1]
        elif time <= self.times[0]:
            return self.values[0]
        else:
            index = bisect_left(self.times, time)

            if self.times[index] == time:
                index += 1

            return self.values[index]

    def slice(self, start_time, stop_time) -> "PiecewiseConstant":
        start_time = Decimal(str(start_time))
        stop_time = Decimal(str(stop_time))

        if start_time == stop_time:
            return PiecewiseConstant(
                [Decimal(0.0), Decimal(0.0)], [Decimal(0.0), Decimal(0.0)]
            )

        start_index = bisect_left(self.times, start_time)
        stop_index = bisect_left(self.times, stop_time)

        if start_time == self.times[start_index]:
            if stop_time == self.times[stop_index]:
                absolute_times = list(self.times[start_index : stop_index + 1])
                values = list(self.values[start_index : stop_index + 1])
            else:
                absolute_times = self.times[start_index:stop_index] + [stop_time]
                values = self.values[start_index:stop_index] + [self.values[stop_index]]
        else:
            if stop_time == self.times[stop_index]:
                absolute_times = [start_time] + self.times[start_index : stop_index + 1]
                values = [self.values[start_index - 1]] + self.values[
                    start_index : stop_index + 1
                ]
            else:
                absolute_times = (
                    [start_time] + self.times[start_index:stop_index] + [stop_time]
                )
                values = (
                    [self.values[start_index - 1]]
                    + self.values[start_index:stop_index]
                    + [self.values[stop_index]]
                )

        values[-1] = values[-2]

        return PiecewiseConstant([time - start_time for time in absolute_times], values)

    def append(self, other: "PiecewiseConstant"):
        return PiecewiseConstant(
            times=self.times + [time + self.times[-1] for time in other.times[1:]],
            values=self.values[:-1] + other.values,
        )


class PiecewiseConstantCodeGen(WaveformVisitor):
    def __init__(self, assignments: Dict[str, Union[numbers.Real, List[numbers.Real]]]):
        self.assignments = assignments
        self.times = []
        self.values = []

    def append_timeseries(self, value, duration):
        if len(self.times) > 0:
            self.times.append(duration + self.times[-1])
            self.values[-1] = value
            self.values.append(value)
        else:
            self.times = [Decimal(0), duration]
            self.values = [value, value]

    def visit_linear(self, ast: waveform.Linear) -> Tuple[List[Decimal], List[Decimal]]:
        duration = ast.duration(**self.assignments)
        start = ast.start(**self.assignments)
        stop = ast.stop(**self.assignments)

        if start != stop:
            raise ValueError(
                "Failed to compile Waveform to piecewise constant, "
                "found non-constant Linear piecce."
            )

        self.append_timeseries(start, duration)

    def visit_constant(
        self, ast: waveform.Constant
    ) -> Tuple[List[Decimal], List[Decimal]]:
        duration = ast.duration(**self.assignments)
        value = ast.value(**self.assignments)

        self.append_timeseries(value, duration)

    def visit_poly(self, ast: waveform.Poly) -> Tuple[List[Decimal], List[Decimal]]:
        order = len(ast.coeffs)
        duration = ast.duration(**self.assignments)

        if order == 0:
            value = Decimal(0)

        elif order == 1:
            value = ast.coeffs[0](**self.assignments)

        elif order == 2:
            start = ast.coeffs[0](**self.assignments)
            stop = start + ast.coeffs[1](**self.assignments) * duration

            if start != stop:
                raise ValueError(
                    "Failed to compile Waveform to piecewise constant, "
                    "found non-constant Polynomial piece."
                )

            value = start

        else:
            raise ValueError(
                "Failed to compile Waveform to piecewise constant,"
                f"found Polynomial of order {order}."
            )

        self.append_timeseries(value, duration)

    def visit_negative(
        self, ast: waveform.Negative
    ) -> Tuple[List[Decimal], List[Decimal]]:
        self.visit(ast.waveform)

        self.values = [-value for value in self.values]

    def visit_scale(self, ast: waveform.Scale) -> Tuple[List[Decimal], List[Decimal]]:
        self.visit(ast.waveform)
        scale = ast.scalar(**self.assignments)
        self.values = [scale * value for value in self.values]

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

        new_pwc = (
            PiecewiseConstantCodeGen(self.assignments)
            .emit(ast.waveform)
            .slice(start_time, stop_time)
        )

        self.times = new_pwc.times
        self.values = new_pwc.values

    def visit_append(self, ast: waveform.Append) -> Tuple[List[Decimal], List[Decimal]]:
        pwc = PiecewiseConstantCodeGen(self.assignments).emit(ast.waveforms[0])

        for sub_expr in ast.waveforms[1:]:
            new_pwc = PiecewiseConstantCodeGen(self.assignments).emit(sub_expr)

            # skip instructions with duration=0
            if new_pwc.times[-1] == Decimal(0):
                continue

            pwc = pwc.append(new_pwc)

        self.times = pwc.times
        self.values = pwc.values

    def visit_sample(self, ast: waveform.Sample) -> Tuple[List[Decimal], List[Decimal]]:
        if ast.interpolation is not waveform.Interpolation.Constant:
            raise ValueError(
                "Failed to compile waveform to piecewise constant, "
                f"found piecewise {ast.interpolation.value} interpolation."
            )
        self.times, values = ast.samples(**self.assignments)
        values[-1] = values[-2]
        self.values = values

    def visit_record(self, ast: waveform.Record) -> Tuple[List[Decimal], List[Decimal]]:
        self.visit(ast.waveform)

    def emit(self, ast: waveform.Waveform) -> PiecewiseConstant:
        self.visit(ast)

        return PiecewiseConstant(times=self.times, values=self.values)
