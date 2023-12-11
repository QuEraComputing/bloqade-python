from bloqade.ir.visitor import BloqadeIRVisitor
from bloqade.ir.control import field, pulse, sequence, waveform


class ValidatePiecewiseConstantChannel(BloqadeIRVisitor):
    def __init__(
        self,
        level_coupling: sequence.LevelCoupling,
        field_name: pulse.FieldName,
        spatial_modulations: field.SpatialModulation,
    ):
        self.level_coupling = level_coupling
        self.field_name = field_name
        self.spatial_modulations = spatial_modulations

    def emit_shape_error(self, node: waveform.Waveform):
        return (
            "failed to compile waveform to piecewise constant. "
            f"found non-constant waveform: {node.print_node()} "
            f"for the {self.level_coupling} {self.field_name} with spatial "
            f"modulation:\n{self.spatial_modulations}"
        )

    def visit_waveform_Linear(self, node: waveform.Linear) -> None:
        if node.start() != node.stop():
            raise ValueError(self.emit_shape_error(node))

    def visit_waveform_Poly(self, node: waveform.Poly) -> None:
        if len(node.coeffs) > 1:
            raise ValueError(self.emit_shape_error(node))

    def visit_waveform_Sample(self, node: waveform.Sample) -> None:
        if node.interpolation != waveform.Interpolation.Constant:
            raise ValueError(self.emit_shape_error(node))

    def visit_waveform_Smooth(self, node: waveform.Smooth) -> None:
        raise ValueError(self.emit_shape_error(node))

    def visit_waveform_PythonFn(self, node: waveform.PythonFn) -> None:
        raise ValueError(self.emit_shape_error(node))

    def visit_sequence_Sequence(self, node: sequence.Sequence) -> None:
        self.visit(node.pulses[self.level_coupling])

    def visit_pulse_Pulse(self, node: pulse.Pulse) -> None:
        self.visit(node.fields[self.field_name])

    def visit_field_Field(self, node: field.Field) -> None:
        self.visit(node.drives[self.spatial_modulations])

    # node type doesn't matter here
    def scan(self, node) -> None:
        self.visit(node)
