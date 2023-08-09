from bloqade.ir.visitor.program_visitor import ProgramVisitor
from bloqade.ir.visitor.waveform_visitor import WaveformVisitor
import bloqade.ir.program as program

# import bloqade.ir.location as location
import bloqade.ir.control.sequence as sequence
import bloqade.ir.control.pulse as pulse
import bloqade.ir.control.field as field
import bloqade.ir.control.waveform as waveform
import bloqade.ir.scalar as scalar
import numbers
from typing import Any, Dict


class StaticAssignWaveform(WaveformVisitor):
    def __init__(self, static_assignments: Dict[str, numbers.Real]):
        self.static_assignments = dict(static_assignments)

    def visit_add(self, ast: waveform.Add) -> Any:
        return waveform.Add(self.visit(ast.left), self.visit(ast.right))

    def visit_alligned(self, ast: waveform.AlignedWaveform) -> Any:
        if isinstance(ast.value, scalar.Scalar):
            value = ast.value.static_assign(**self.static_assignments)
        else:
            value = ast.value

        return waveform.AlignedWaveform(self.visit(ast.waveform), ast.alignment, value)

    def visit_append(self, ast: waveform.Append) -> Any:
        return waveform.Append(list(map(self.visit, ast.waveforms)))

    def visit_constant(self, ast: waveform.Constant) -> Any:
        value = ast.value.statis_assign(**self.static_assignments)
        duration = ast.duration.static_assign(**self.static_assignments)
        return waveform.Constant(value, duration)

    def visit_smooth(self, ast: waveform.Smooth) -> Any:
        static_radius = ast.radius.static_assign(**self.static_assignments)
        return waveform.Smooth(static_radius, ast.kernel, self.visit(ast.waveform))

    def visit_poly(self, ast: waveform.Poly) -> Any:
        checkpoints = [
            checkpoint.static_assign(**self.static_assignments)
            for checkpoint in ast.checkpoints
        ]
        duration = ast.duration.static_assign(**self.static_assignments)
        return waveform.Poly(checkpoints, duration)

    def visit_python_fn(self, ast: waveform.PythonFn) -> Any:
        pass

    def visit_negative(self, ast: waveform.Negative) -> Any:
        return super().visit_negative(ast)

    def visit_linear(self, ast: waveform.Linear) -> Any:
        return super().visit_linear(ast)

    def visit_record(self, ast: waveform.Record) -> Any:
        return super().visit_record(ast)

    def visit_sample(self, ast: waveform.Sample) -> Any:
        return super().visit_sample(ast)

    def visit_scale(self, ast: waveform.Scale) -> Any:
        return super().visit_scale(ast)

    def visit_slice(self, ast: waveform.Slice) -> Any:
        return super().visit_slice(ast)

    def emit(self, ast: waveform.Waveform) -> waveform.Waveform:
        return self.visit(ast)


class StaticAssignProgram(ProgramVisitor):
    def __init__(self, static_assignments: Dict[str, numbers.Real]):
        self.static_assignments = dict(static_assignments)

    def visit_sequence(self, ast: sequence.SequenceExpr) -> sequence.SequenceExpr:
        match ast:
            case sequence.Sequence(pulses):
                return sequence.Sequence(
                    {
                        coupling_name: self.visit(sub_pulse)
                        for coupling_name, sub_pulse in pulses.items()
                    }
                )
            case sequence.Append(sequences):
                return sequence.Append(list(map(self.visit, sequences)))
            case sequence.Slice(sub_sequence, interval):
                return sequence.Slice(self.visit(sub_sequence), interval)
            case sequence.NamedSequence(sub_sequence, name):
                return sequence.NamedSequence(self.visit(sub_sequence), name)

    def visit_pulse(self, ast: pulse.PulseExpr) -> pulse.PulseExpr:
        match ast:
            case pulse.Pulse(fields):
                return pulse.Pulse(
                    {
                        field_name: self.visit(sub_field)
                        for field_name, sub_field in fields.items()
                    }
                )
            case pulse.Append(pulses):
                return pulse.Append(list(map(self.visit, pulses)))
            case pulse.Slice(sub_pulse, interval):
                return pulse.Slice(self.visit(sub_pulse), interval)
            case pulse.NamedPulse(name, sub_pulse):
                return pulse.NamedPulse(name, self.visit(sub_pulse))

    def visit_field(self, ast: field.Field) -> field.Field:
        return field.Field(
            {self.visit(sm): self.visit(wf) for sm, wf in ast.value.items()}
        )

    def visit_spatial_modulation(
        self, ast: field.SpatialModulation
    ) -> field.SpatialModulation:
        pass

    def visit_waveform(self, ast: waveform.Waveform) -> waveform.Waveform:
        return StaticAssignWaveform(self.static_assignments).emit(ast)

    def emit(self, ast: program.Program) -> program.Program:
        return program.Program(self.visit(ast.register), self.visit(ast.sequence))
