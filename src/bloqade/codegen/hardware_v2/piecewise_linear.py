from functools import reduce
from bloqade.ir.visitor import BloqadeIRVisitor
from bloqade.ir.control import waveform, field, pulse, sequence
import bloqade.ir.analog_circuit as analog_circuit

from beartype.typing import List
from beartype import beartype
from pydantic.dataclasses import dataclass
from bisect import bisect_left, bisect_right
from decimal import Decimal


@dataclass(frozen=True)
class PiecewiseLinear:
    """PiecewiseLinear represents a piecewise linear function.


    Contains methods for evaluating the function at a given time and slicing
    since these are common operations in the code generation process.
    """

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
            if stop_time == self.times[stop_index]:
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

    @staticmethod
    def append(left: "PiecewiseLinear", right: "PiecewiseLinear") -> "PiecewiseLinear":
        return PiecewiseLinear(
            times=left.times + [time + left.times[-1] for time in right.times[1:]],
            values=left.values + right.values[1:],
        )


class GeneratePiecewiseLinearChannel(BloqadeIRVisitor):
    valid_nodes = {
        waveform.Constant,
        waveform.Linear,
        waveform.Poly,
        waveform.Sample,
        waveform.Add,
        waveform.Append,
        waveform.Slice,
        waveform.Negative,
        waveform.Scale,
        field.Field,
        pulse.Pulse,
        pulse.NamedPulse,
        pulse.Slice,
        pulse.Append,
        sequence.Sequence,
        sequence.NamedSequence,
        sequence.Slice,
        sequence.Append,
        analog_circuit.AnalogCircuit,
    }

    @beartype
    def __init__(
        self,
        level_coupling: sequence.LevelCoupling,
        field_name: pulse.FieldName,
        spatial_modulations: field.SpatialModulation,
    ):
        self.level_coupling = level_coupling
        self.field_name = field_name
        self.spatial_modulations = spatial_modulations

    def visit_waveform_Constant(self, node: waveform.Constant) -> PiecewiseLinear:
        return PiecewiseLinear(
            [Decimal(0), node.duration()], [node.value(), node.value()]
        )

    def visit_waveform_Linear(self, node: waveform.Linear) -> PiecewiseLinear:
        return PiecewiseLinear(
            [Decimal(0), node.duration()], [node.start(), node.stop()]
        )

    def visit_waveform_Poly(self, node: waveform.Poly) -> PiecewiseLinear:
        duration = node.duration()
        start = node.eval_decimal(0)
        stop = node.eval_decimal(duration)

        return PiecewiseLinear(
            [Decimal(0), duration],
            [start, stop],
        )

    def visit_waveform_Sample(self, node: waveform.Sample) -> PiecewiseLinear:
        times, values = node.samples()
        return PiecewiseLinear(times, values)

    def visit_waveform_Add(self, node: waveform.Add) -> PiecewiseLinear:
        left = self.visit(node.left)
        right = self.visit(node.right)

        times = sorted(list(set(left.times + right.times)))
        values = [left.eval(t) + right.eval(t) for t in times]

        return PiecewiseLinear(times, values)

    def visit_waveform_Append(self, node: waveform.Append) -> PiecewiseLinear:
        return reduce(PiecewiseLinear.append, map(self.visit, node.waveforms))

    def visit_waveform_Slice(self, node: waveform.Slice) -> PiecewiseLinear:
        pwl = self.visit(node.waveform)
        return pwl.slice(node.start(), node.stop())

    def visit_waveform_Negative(self, node: waveform.Negative) -> PiecewiseLinear:
        pwl = self.visit(node.waveform)
        return PiecewiseLinear(pwl.times, [-v for v in pwl.values])

    def visit_waveform_Scale(self, node: waveform.Scale) -> PiecewiseLinear:
        pwl = self.visit(node.waveform)
        return PiecewiseLinear(pwl.times, [node.scalar() * v for v in pwl.values])

    def visit_field_Field(self, node: field.Field) -> PiecewiseLinear:
        return self.visit(node.drives[self.spatial_modulations])

    def visit_pulse_Pulse(self, node: pulse.Pulse) -> PiecewiseLinear:
        return self.visit(node.fields[self.field_name])

    def visit_pulse_NamedPulse(self, node: pulse.NamedPulse) -> PiecewiseLinear:
        return self.visit(node.pulse)

    def visit_pulse_Slice(self, node: pulse.Slice) -> PiecewiseLinear:
        return self.visit(node.pulse).slice(node.start(), node.stop())

    def visit_pulse_Append(self, node: pulse.Append) -> PiecewiseLinear:
        return reduce(PiecewiseLinear.append, map(self.visit, node.pulses))

    def visit_sequence_Sequence(self, node: sequence.Sequence) -> PiecewiseLinear:
        return self.visit(node.pulses[self.level_coupling])

    def visit_sequence_NamedSequence(
        self, node: sequence.NamedSequence
    ) -> PiecewiseLinear:
        return self.visit(node.sequence)

    def visit_sequence_Slice(self, node: sequence.Slice) -> PiecewiseLinear:
        return self.visit(node.sequence).slice(node.start(), node.stop())

    def visit_sequence_Append(self, node: sequence.Append) -> PiecewiseLinear:
        return reduce(PiecewiseLinear.append, map(self.visit, node.sequences))

    def visit_analog_circuit_AnalogCircuit(
        self, node: analog_circuit.AnalogCircuit
    ) -> PiecewiseLinear:
        return self.visit(node.sequence)

    # add another visit method for the new type
    # every visitor method should return a PiecewiseLinear object
    # Then we can use the PiecewiseLinear object to combine the
    # resulting waveforms into a single waveform using the AST node
    # to determine which transformation to apply, e.g. add, scale, etc.
    def visit(self, node) -> PiecewiseLinear:
        if type(node) not in self.valid_nodes:
            raise TypeError(
                f"Expected one of {self.valid_nodes}, got {type(node)} instead."
            )

        return super().visit(node)
