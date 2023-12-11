import bloqade.ir.control.waveform as waveform
from bloqade.ir.visitor import BloqadeIRVisitor

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

            m = (self.values[index + 1] - self.values[index]) / (
                self.times[index + 1] - self.times[index]
            )
            t = time - self.times[index]
            b = self.values[index]

            return m * t + b

    def slice(self, start_time: Decimal, stop_time: Decimal) -> "PiecewiseLinear":
        start_time = (
            Decimal(str(start_time))
            if not isinstance(start_time, Decimal)
            else start_time
        )
        stop_time = (
            Decimal(str(stop_time)) if not isinstance(stop_time, Decimal) else stop_time
        )

        if start_time == stop_time:
            return PiecewiseLinear(
                [Decimal(0.0), Decimal(0.0)], [Decimal(0.0), Decimal(0.0)]
            )

        start_index = bisect_left(self.times, start_time)
        stop_index = bisect_left(self.times, stop_time)
        start_value = self.eval(start_time)
        stop_value = self.eval(stop_time)

        if start_time == self.times[start_index]:
            if stop_time == self.times[start_index]:
                absolute_times = list(self.times[start_index : stop_index + 1])
                values = list(self.values[start_index : stop_index + 1])
            else:
                absolute_times = self.times[start_index:stop_index] + [stop_time]
                values = self.values[start_index:stop_index] + [stop_value]
        else:
            if stop_time == self.times[stop_index]:
                absolute_times = [start_time] + self.times[start_index : stop_index + 1]
                values = [start_value] + self.values[start_index : stop_index + 1]
            else:
                absolute_times = (
                    [start_time] + self.times[start_index:stop_index] + [stop_time]
                )
                values = (
                    [start_value] + self.values[start_index:stop_index] + [stop_value]
                )

        return PiecewiseLinear([time - start_time for time in absolute_times], values)

    def append(self, other: "PiecewiseLinear"):
        assert self.values[-1] == other.values[0]

        return PiecewiseLinear(
            times=self.times + [time + self.times[-1] for time in other.times[1:]],
            values=self.values + other.values[1:],
        )


class PiecewiseLinearCodeGen(BloqadeIRVisitor):
    def __init__(self, assignments: Dict[str, Union[numbers.Real, List[numbers.Real]]]):
        self.assignments = assignments
        self.times = []
        self.values = []

    @staticmethod
    def check_continiuity(left, right):
        if left != right:
            diff = abs(left - right)
            raise ValueError(
                f"discontinuity with a jump of {diff} found when compiling to "
                "piecewise linear."
            )

    def append_timeseries(self, start, stop, duration):
        if len(self.times) == 0:
            self.times = [Decimal(0), duration]
            self.values = [start, stop]
        else:
            self.check_continiuity(self.values[-1], start)

            self.times.append(duration + self.times[-1])
            self.values.append(stop)

    def visit_waveform_Linear(
        self, node: waveform.Linear
    ) -> Tuple[List[Decimal], List[Decimal]]:
        duration = node.duration(**self.assignments)
        start = node.start(**self.assignments)
        stop = node.stop(**self.assignments)
        self.append_timeseries(start, stop, duration)

    def visit_waveform_Constant(
        self, node: waveform.Constant
    ) -> Tuple[List[Decimal], List[Decimal]]:
        duration = node.duration(**self.assignments)
        value = node.value(**self.assignments)
        self.append_timeseries(value, value, duration)

    def visit_waveform_Poly(
        self, node: waveform.Poly
    ) -> Tuple[List[Decimal], List[Decimal]]:
        order = len(node.coeffs) - 1
        duration = node.duration(**self.assignments)

        if len(node.coeffs) == 0:
            start = Decimal(0)
            stop = Decimal(0)
        elif len(node.coeffs) == 1:
            start = node.coeffs[0](**self.assignments)
            stop = start
        elif len(node.coeffs) == 2:
            start = node.coeffs[0](**self.assignments)
            stop = start + node.coeffs[1](**self.assignments) * duration
        else:
            raise ValueError(
                "Failed to compile Waveform to piecewise linear,"
                f"found Polynomial of order {order}."
            )

        self.append_timeseries(start, stop, duration)

    def visit_waveform_Negative(
        self, node: waveform.Negative
    ) -> Tuple[List[Decimal], List[Decimal]]:
        self.visit(node.waveform)
        self.values = [-value for value in self.values]

    def visit_waveform_Scale(
        self, node: waveform.Scale
    ) -> Tuple[List[Decimal], List[Decimal]]:
        self.visit(node.waveform)
        scaler = node.scalar(**self.assignments)
        self.values = [scaler * value for value in self.values]

    def visit_waveform_Slice(
        self, node: waveform.Slice
    ) -> Tuple[List[Decimal], List[Decimal]]:
        duration = node.waveform.duration(**self.assignments)

        start_time = node.start(**self.assignments)
        stop_time = node.stop(**self.assignments)

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

        pwl = PiecewiseLinearCodeGen(self.assignments).emit(node.waveform)
        new_pwl = pwl.slice(start_time, stop_time)

        self.times = new_pwl.times
        self.values = new_pwl.values

    def visit_waveform_Append(
        self, node: waveform.Append
    ) -> Tuple[List[Decimal], List[Decimal]]:
        pwl = PiecewiseLinearCodeGen(self.assignments).emit(node.waveforms[0])

        for sub_expr in node.waveforms[1:]:
            new_pwl = PiecewiseLinearCodeGen(self.assignments).emit(sub_expr)

            # skip instructions with duration=0
            if new_pwl.times[-1] == Decimal(0):
                continue

            self.check_continiuity(pwl.values[-1], new_pwl.values[0])
            pwl = pwl.append(new_pwl)

        self.times = pwl.times
        self.values = pwl.values

    def visit_waveform_Sample(
        self, node: waveform.Sample
    ) -> Tuple[List[Decimal], List[Decimal]]:
        if node.interpolation is not waveform.Interpolation.Linear:
            raise ValueError(
                "Failed to compile waveform to piecewise linear, "
                f"found piecewise {node.interpolation.value} interpolation."
            )

        self.times, self.values = node.samples(**self.assignments)

    def emit(self, node: waveform.Waveform) -> PiecewiseLinear:
        self.visit(node)
        return PiecewiseLinear(self.times, self.values)
