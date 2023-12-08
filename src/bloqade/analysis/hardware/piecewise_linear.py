from bloqade.ir.visitor import BloqadeIRVisitor
from bloqade.ir import scalar
from bloqade.ir.control import field, pulse, sequence, waveform
from decimal import Decimal


class ValidatePiecewiseLinearChannel(BloqadeIRVisitor):
    def __init__(
        self,
        level_coupling: sequence.LevelCoupling,
        field_name: pulse.FieldName,
        spatial_modulations: field.SpatialModulation,
    ):
        self.level_coupling = level_coupling
        self.field_name = field_name
        self.spatial_modulations = spatial_modulations

    def check_continuous(
        self,
        time: scalar.Scalar,
        level: str,
        lhs: waveform.Waveform,
        rhs: waveform.Waveform,
    ):
        diff = abs(lhs.eval_decimal(lhs.duration()) - rhs.eval_decimal(0))
        if diff != Decimal("0"):
            raise ValueError(
                f"failed to compile waveform to piecewise linear. On the {level} level "
                f"a discontinuity of {diff} was found at time={time()}"
                f"for the {self.level_coupling} {self.field_name} with spatial "
                f"modulation:\n{self.spatial_modulations}"
            )

    def emit_shape_error(self, node: waveform.Waveform):
        return (
            "failed to compile waveform to piecewise linear. "
            f"found non-linear waveform: {node.print_node()} "
            f"for the {self.level_coupling} {self.field_name} with spatial "
            f"modulation:\n{self.spatial_modulations}"
        )

    def visit_waveform_Poly(self, node: waveform.Poly) -> None:
        if len(node.coeffs) > 2:
            raise ValueError(self.emit_shape_error(node))

    def visit_waveform_Sample(self, node: waveform.Sample) -> None:
        if node.interpolation != waveform.Interpolation.Linear:
            raise ValueError(self.emit_shape_error(node))

    def visit_waveform_Smooth(self, node: waveform.Smooth) -> None:
        raise ValueError(self.emit_shape_error(node))

    def visit_waveform_PythonFn(self, node: waveform.PythonFn) -> None:
        raise ValueError(self.emit_shape_error(node))

    def visit_waveform_Append(self, node: waveform.Append) -> None:
        for wf in node.waveforms:
            self.visit(wf)

        result = node.waveforms[0]

        time = result.duration

        for lhs, rhs in zip(node.waveforms[:-1], node.waveforms[1:]):
            self.check_continuous(time, "Waveform", lhs, rhs)
            time = time + lhs.duration

    def visit_sequence_Append(self, node: sequence.Append) -> waveform.Waveform:
        wfs = list(map(self.visit, node.sequences))

        result = wfs[0]

        time = result.duration

        for lhs, rhs in zip(wfs[:-1], wfs[1:]):
            self.check_continuous(time, "Sequence", lhs, rhs)
            result = result.append(rhs)
            time = time + lhs.duration

        return result

    def visit_sequence_Slice(self, node: sequence.Slice) -> waveform.Waveform:
        interval = node.interval
        wf = self.visit(node.sequence)
        return wf[interval.start : interval.stop]

    def visit_sequence_NamedSequence(
        self, node: sequence.NamedSequence
    ) -> waveform.Waveform:
        return self.visit(node.sequence)

    def visit_sequence_Sequence(self, node: sequence.Sequence) -> waveform.Waveform:
        return self.visit(node.pulses[self.level_coupling])

    def visit_pulse_Append(self, node: pulse.Append) -> waveform.Waveform:
        wfs = list(map(self.visit, node.pulses))

        result = wfs[0]

        time = result.duration

        for lhs, rhs in zip(wfs[:-1], wfs[1:]):
            self.check_continuous(time, "Pulse", lhs, rhs)
            result = result.append(rhs)
            time = time + lhs.duration

        return result

    def visit_pulse_Slice(self, node: pulse.Slice) -> waveform.Waveform:
        interval = node.interval
        wf = self.visit(node.pulse)
        return wf[interval.start : interval.stop]

    def visit_pulse_NamedPulse(self, node: pulse.NamedPulse) -> waveform.Waveform:
        return self.visit(node.pulse)

    def visit_pulse_Pulse(self, node: pulse.Pulse) -> waveform.Waveform:
        return self.visit(node.fields[self.field_name])

    def visit_field_Field(self, node: field.Field) -> waveform.Waveform:
        wf = node.drives[self.spatial_modulations]

        self.visit(wf)

        return wf

    # node type doesn't matter here
    def scan(self, node) -> None:
        self.visit(node)
