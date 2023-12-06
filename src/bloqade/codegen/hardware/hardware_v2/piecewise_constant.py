from functools import reduce
from bloqade.ir.control import waveform, pulse, sequence, field
from bloqade.ir import analog_circuit

from bloqade.ir.visitor import BloqadeIRVisitor

from beartype.typing import List
from beartype import beartype
from pydantic.dataclasses import dataclass
from bisect import bisect_left
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

    @staticmethod
    def append(
        left: "PiecewiseConstant", other: "PiecewiseConstant"
    ) -> "PiecewiseConstant":
        return PiecewiseConstant(
            times=left.times + [time + left.times[-1] for time in other.times[1:]],
            values=left.values[:-1] + other.values,
        )


class GeneratePiecewiseConstantChannel(BloqadeIRVisitor):
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
        return PiecewiseConstant(times, values)

    def visit_waveform_Add(self, node: waveform.Add) -> PiecewiseConstant:
        lhs = self.visit(node.lhs)
        rhs = self.visit(node.rhs)

        times = sorted(list(set(lhs.times + rhs.times)))
        values = [lhs.eval(t) + rhs.eval(t) for t in times]

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
        return super().visit(node)
