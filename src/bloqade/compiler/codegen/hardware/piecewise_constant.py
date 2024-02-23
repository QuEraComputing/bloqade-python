from functools import reduce
from bloqade.ir.control import waveform, pulse, sequence, field
from bloqade.ir import analog_circuit

from bloqade.ir.visitor import BloqadeIRVisitor

from beartype.typing import List
from beartype import beartype
from pydantic.dataclasses import dataclass
from bisect import bisect_right, bisect_left
from decimal import Decimal


@dataclass(frozen=True)
class PiecewiseConstant:
    times: List[Decimal]
    values: List[Decimal]

    def eval(self, time):
        if time < 0 or time > self.times[-1]:
            return Decimal("0")

        i = bisect_right(self.times[1:], time)

        return self.values[i]

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

    @staticmethod
    def append(
        left: "PiecewiseConstant", right: "PiecewiseConstant"
    ) -> "PiecewiseConstant":
        new_times = left.times + [time + left.times[-1] for time in right.times[1:]]
        new_values = left.values[:-1] + right.values
        return PiecewiseConstant(
            times=new_times,
            values=new_values,
        )


class GeneratePiecewiseConstantChannel(BloqadeIRVisitor):
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

    def visit_waveform_Constant(self, node: waveform.Constant) -> PiecewiseConstant:
        return PiecewiseConstant(
            [Decimal(0), node.duration()], [node.value(), node.value()]
        )

    def visit_waveform_Linear(self, node: waveform.Linear) -> PiecewiseConstant:
        return PiecewiseConstant(
            [Decimal(0), node.duration()], [node.start(), node.start()]
        )

    def visit_waveform_Poly(self, node: waveform.Poly) -> PiecewiseConstant:
        duration = node.duration()
        start = node.eval_decimal(0)

        return PiecewiseConstant(
            [Decimal(0), duration],
            [start, start],
        )

    def visit_waveform_Sample(self, node: waveform.Sample) -> PiecewiseConstant:
        times, values = node.samples()
        values[-1] = values[-2]

        return PiecewiseConstant(times, values)

    def visit_waveform_Add(self, node: waveform.Add) -> PiecewiseConstant:
        left = self.visit(node.left)
        right = self.visit(node.right)

        times = sorted(list(set(left.times + right.times)))
        values = [left.eval(t) + right.eval(t) for t in times]

        return PiecewiseConstant(times, values)

    def visit_waveform_Append(self, node: waveform.Append) -> PiecewiseConstant:
        return reduce(PiecewiseConstant.append, map(self.visit, node.waveforms))

    def visit_waveform_Slice(self, node: waveform.Slice) -> PiecewiseConstant:
        pwl = self.visit(node.waveform)
        return pwl.slice(node.start(), node.stop())

    def visit_waveform_Negative(self, node: waveform.Negative) -> PiecewiseConstant:
        pwl = self.visit(node.waveform)
        return PiecewiseConstant(pwl.times, [-v for v in pwl.values])

    def visit_waveform_Scale(self, node: waveform.Scale) -> PiecewiseConstant:
        pwl = self.visit(node.waveform)
        return PiecewiseConstant(pwl.times, [node.scalar() * v for v in pwl.values])

    def visit_field_Field(self, node: field.Field) -> PiecewiseConstant:
        return self.visit(node.drives[self.spatial_modulations])

    def visit_pulse_Pulse(self, node: pulse.Pulse) -> PiecewiseConstant:
        return self.visit(node.fields[self.field_name])

    def visit_pulse_NamedPulse(self, node: pulse.NamedPulse) -> PiecewiseConstant:
        return self.visit(node.pulse)

    def visit_pulse_Slice(self, node: pulse.Slice) -> PiecewiseConstant:
        return self.visit(node.pulse).slice(node.start(), node.stop())

    def visit_pulse_Append(self, node: pulse.Append) -> PiecewiseConstant:
        return reduce(PiecewiseConstant.append, map(self.visit, node.pulses))

    def visit_sequence_Sequence(self, node: sequence.Sequence) -> PiecewiseConstant:
        return self.visit(node.pulses[self.level_coupling])

    def visit_sequence_NamedSequence(
        self, node: sequence.NamedSequence
    ) -> PiecewiseConstant:
        return self.visit(node.sequence)

    def visit_sequence_Slice(self, node: sequence.Slice) -> PiecewiseConstant:
        return self.visit(node.sequence).slice(node.start(), node.stop())

    def visit_sequence_Append(self, node: sequence.Append) -> PiecewiseConstant:
        return reduce(PiecewiseConstant.append, map(self.visit, node.sequences))

    def visit_analog_circuit_AnalogCircuit(
        self, node: analog_circuit.AnalogCircuit
    ) -> PiecewiseConstant:
        return self.visit(node.sequence)

    # add another visit method for the new type
    # every visitor method should return a PiecewiseConstant object
    # Then we can use the PiecewiseConstant object to combine the
    # resulting waveforms into a single waveform using the AST node
    # to determine which transformation to apply, e.g. add, scale, etc.
    def visit(self, node) -> PiecewiseConstant:
        if type(node) not in self.valid_nodes:
            raise TypeError(
                f"Expected one of {self.valid_nodes}, got {type(node)} instead."
            )

        return super().visit(node)
