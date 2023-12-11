import bloqade.ir.control.waveform as waveform
from bloqade.ir.visitor import BloqadeIRVisitor

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


class PiecewiseConstantCodeGen(BloqadeIRVisitor):
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

    def visit_waveform_Linear(
        self, node: waveform.Linear
    ) -> Tuple[List[Decimal], List[Decimal]]:
        duration = node.duration(**self.assignments)
        start = node.start(**self.assignments)
        stop = node.stop(**self.assignments)

        if start != stop:
            raise ValueError(
                "Failed to compile Waveform to piecewise constant, "
                "found non-constant Linear piece."
            )

        self.append_timeseries(start, duration)

    def visit_waveform_Constant(
        self, node: waveform.Constant
    ) -> Tuple[List[Decimal], List[Decimal]]:
        duration = node.duration(**self.assignments)
        value = node.value(**self.assignments)

        self.append_timeseries(value, duration)

    def visit_waveform_Poly(
        self, node: waveform.Poly
    ) -> Tuple[List[Decimal], List[Decimal]]:
        order = len(node.coeffs) - 1
        duration = node.duration(**self.assignments)

        if len(node.coeffs) == 0:
            value = Decimal(0)

        elif len(node.coeffs) == 1:
            value = node.coeffs[0](**self.assignments)

        elif len(node.coeffs) == 2:
            start = node.coeffs[0](**self.assignments)
            stop = start + node.coeffs[1](**self.assignments) * duration

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

    def visit_waveform_Negative(
        self, node: waveform.Negative
    ) -> Tuple[List[Decimal], List[Decimal]]:
        self.visit(node.waveform)

        self.values = [-value for value in self.values]

    def visit_waveform_Scale(
        self, node: waveform.Scale
    ) -> Tuple[List[Decimal], List[Decimal]]:
        self.visit(node.waveform)
        scale = node.scalar(**self.assignments)
        self.values = [scale * value for value in self.values]

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

        new_pwc = (
            PiecewiseConstantCodeGen(self.assignments)
            .emit(node.waveform)
            .slice(start_time, stop_time)
        )

        self.times = new_pwc.times
        self.values = new_pwc.values

    def visit_waveform_Append(
        self, node: waveform.Append
    ) -> Tuple[List[Decimal], List[Decimal]]:
        pwc = PiecewiseConstantCodeGen(self.assignments).emit(node.waveforms[0])

        for sub_expr in node.waveforms[1:]:
            new_pwc = PiecewiseConstantCodeGen(self.assignments).emit(sub_expr)

            # skip instructions with duration=0
            if new_pwc.times[-1] == Decimal(0):
                continue

            pwc = pwc.append(new_pwc)

        self.times = pwc.times
        self.values = pwc.values

    def visit_waveform_Sample(
        self, node: waveform.Sample
    ) -> Tuple[List[Decimal], List[Decimal]]:
        if node.interpolation is not waveform.Interpolation.Constant:
            raise ValueError(
                "Failed to compile waveform to piecewise constant, "
                f"found piecewise {node.interpolation.value} interpolation."
            )
        self.times, values = node.samples(**self.assignments)
        values[-1] = values[-2]
        self.values = values

    def emit(self, node: waveform.Waveform) -> PiecewiseConstant:
        self.visit(node)

        return PiecewiseConstant(times=self.times, values=self.values)
