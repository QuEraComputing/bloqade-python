import bloqade.ir.location as location
import bloqade.ir.control.sequence as sequence
import bloqade.ir.control.pulse as pulse
import bloqade.ir.control.field as field
import bloqade.ir.control.waveform as waveform
import bloqade.ir.scalar as scalar
import bloqade.ir.analog_circuit as analog_circuit

from bloqade.ir.visitor.analog_circuit import (
    # AnalogCircuitVisitor,
    AnalogCircuitVisitorV2,
)
from bloqade.ir.visitor.location import LocationVisitor
from bloqade.ir.visitor.waveform import WaveformVisitor
from bloqade.ir.visitor.scalar import ScalarVisitor

import numbers
from typing import Any, Dict, Union
from decimal import Decimal


class AssignScalar(ScalarVisitor):
    def __init__(self, mapping: Dict[str, Decimal]):
        self.mapping = dict(mapping)

    def visit_literal(self, ast: scalar.Literal) -> scalar.Scalar:
        return ast

    def visit_variable(
        self, ast: scalar.Variable
    ) -> Union[scalar.Literal, scalar.Variable]:
        if ast.name in self.mapping:
            return scalar.AssignedVariable(ast.name, self.mapping[ast.name])

        return ast

    def visit_assigned_variable(
        self, ast: scalar.Variable
    ) -> Union[scalar.Literal, scalar.AssignedVariable]:
        if ast.name in self.mapping:
            raise ValueError(f"Variable {ast.name} already assigned to {ast.value}.")

        return ast

    def visit_negative(self, ast: scalar.Negative) -> scalar.Scalar:
        return -self.visit(ast.expr)

    def visit_add(self, ast: scalar.Add) -> scalar.Scalar:
        return self.visit(ast.lhs) + self.visit(ast.rhs)

    def visit_div(self, ast: scalar.Div) -> scalar.Scalar:
        return self.visit(ast.lhs) / self.visit(ast.rhs)

    def visit_mul(self, ast: scalar.Mul) -> scalar.Scalar:
        return self.visit(ast.lhs) * self.visit(ast.rhs)

    def visit_min(self, ast: scalar.Min) -> scalar.Scalar:
        return scalar.Scalar.canonicalize(
            scalar.Min(frozenset(list(map(self.visit, ast.scalars))))
        )

    def visit_max(self, ast: scalar.Min) -> scalar.Scalar:
        return scalar.Scalar.canonicalize(
            scalar.Max(frozenset(list(map(self.visit, ast.scalars))))
        )

    def emit(self, ast: scalar.Scalar) -> scalar.Scalar:
        # canonicalize at the end
        return scalar.Scalar.canonicalize(self.visit(ast))


class AssignWaveform(WaveformVisitor):
    def __init__(self, mapping: Dict[str, numbers.Real]):
        self.scalar_visitor = AssignScalar(mapping)
        self.mapping = dict(mapping)

    def visit_constant(self, ast: waveform.Constant) -> Any:
        value = self.scalar_visitor.emit(ast.value)
        duration = self.scalar_visitor.emit(ast.duration)
        return waveform.Constant(value, duration)

    def visit_linear(self, ast: waveform.Linear) -> Any:
        start = self.scalar_visitor.emit(ast.start)
        stop = self.scalar_visitor.emit(ast.stop)
        duration = self.scalar_visitor.emit(ast.duration)
        return waveform.Linear(start, stop, duration)

    def visit_poly(self, ast: waveform.Poly) -> Any:
        checkpoints = list(map(self.scalar_visitor.emit, ast.coeffs))
        duration = self.scalar_visitor.emit(ast.duration)
        return waveform.Poly(checkpoints, duration)

    def visit_python_fn(self, ast: waveform.PythonFn) -> Any:
        new_ast = waveform.PythonFn(ast.fn, self.scalar_visitor.emit(ast.duration))
        new_ast.parameters = list(map(self.scalar_visitor.emit, ast.parameters))
        return new_ast

    def visit_add(self, ast: waveform.Add) -> Any:
        return waveform.Add(self.visit(ast.left), self.visit(ast.right))

    def visit_alligned(self, ast: waveform.AlignedWaveform) -> Any:
        if isinstance(ast.value, scalar.Scalar):
            value = self.scalar_visitor.emit(ast.value)
        else:
            value = ast.value

        return waveform.AlignedWaveform(self.visit(ast.waveform), ast.alignment, value)

    def visit_append(self, ast: waveform.Append) -> Any:
        return waveform.Append(list(map(self.visit, ast.waveforms)))

    def visit_smooth(self, ast: waveform.Smooth) -> Any:
        static_radius = self.scalar_visitor.emit(ast.radius)
        return waveform.Smooth(static_radius, ast.kernel, self.visit(ast.waveform))

    def visit_negative(self, ast: waveform.Negative) -> Any:
        return waveform.Negative(self.visit(ast.waveform))

    def visit_record(self, ast: waveform.Record) -> Any:
        if ast.var.name in self.mapping:
            return self.visit(ast.waveform)
        else:
            return waveform.Record(self.visit(ast.waveform), ast.var)

    def visit_sample(self, ast: waveform.Sample) -> Any:
        dt = self.scalar_visitor.emit(ast.dt)
        return waveform.Sample(self.visit(ast.waveform), ast.interpolation, dt)

    def visit_scale(self, ast: waveform.Scale) -> Any:
        scale = self.scalar_visitor.emit(ast.scalar)
        return waveform.Scale(scale, self.visit(ast.waveform))

    def visit_slice(self, ast: waveform.Slice) -> Any:
        start = ast.interval.start
        stop = ast.interval.stop

        if start is not None:
            start = self.scalar_visitor.emit(start)

        if stop is not None:
            stop = self.scalar_visitor.emit(stop)

        return waveform.Slice(self.visit(ast.waveform), scalar.Interval(start, stop))

    def emit(self, ast: waveform.Waveform) -> waveform.Waveform:
        return waveform.Waveform.canonicalize(self.visit(ast))


class AssignLocation(LocationVisitor):
    def __init__(self, mapping: Dict[str, numbers.Real]):
        self.mapping = dict(mapping)
        self.scalar_visitor = AssignScalar(mapping)

    def visit_chain(self, ast: location.Chain) -> location.Chain:
        return location.Chain(
            ast.shape[0], self.scalar_visitor.emit(ast.lattice_spacing)
        )

    def visit_square(self, ast: location.Square) -> location.Square:
        return location.Square(
            ast.shape[0], self.scalar_visitor.emit(ast.lattice_spacing)
        )

    def visit_rectangular(self, ast: location.Rectangular) -> location.Rectangular:
        return location.Rectangular(
            ast.shape[0],
            ast.shape[1],
            self.scalar_visitor.emit(ast.lattice_spacing_x),
            self.scalar_visitor.emit(ast.lattice_spacing_y),
        )

    def visit_triangular(self, ast: location.Triangular) -> location.Triangular:
        return location.Triangular(
            ast.shape[0], self.scalar_visitor.emit(ast.lattice_spacing)
        )

    def visit_honeycomb(self, ast: location.Honeycomb) -> location.Honeycomb:
        return location.Honeycomb(
            ast.shape[0], self.scalar_visitor.emit(ast.lattice_spacing)
        )

    def visit_kagome(self, ast: location.Kagome) -> location.Kagome:
        return location.Kagome(
            ast.shape[0], self.scalar_visitor.emit(ast.lattice_spacing)
        )

    def visit_lieb(self, ast: location.Lieb) -> location.Lieb:
        return location.Lieb(
            ast.shape[0], self.scalar_visitor.emit(ast.lattice_spacing)
        )

    def visit_list_of_locations(
        self, ast: location.ListOfLocations
    ) -> location.ListOfLocations:
        return location.ListOfLocations(list(map(self.visit, ast.location_list)))

    def visit_location_info(self, ast: location.LocationInfo) -> location.LocationInfo:
        return location.LocationInfo(
            tuple(map(self.scalar_visitor.emit, ast.position)),
            bool(ast.filling.value),
        )

    def visit_parallel_register(
        self, ast: location.ParallelRegister
    ) -> location.ParallelRegister:
        return location.ParallelRegister(
            self.visit(ast._register), self.scalar_visitor.emit(ast._cluster_spacing)
        )


class AssignAnalogCircuit(AnalogCircuitVisitorV2):
    def __init__(self, mapping: Dict[str, numbers.Real]):
        self.waveform_visitor = AssignWaveform(mapping)
        self.scalar_visitor = AssignScalar(mapping)
        self.location_visitor = AssignLocation(mapping)
        self.mapping = dict(mapping)

    def visit_analog_circuit(self, ast: analog_circuit.AnalogCircuit) -> Any:
        return analog_circuit.AnalogCircuit(
            self.visit(ast.register), self.visit(ast.sequence)
        )

    def visit_register(self, ast: location.AtomArrangement) -> location.AtomArrangement:
        return self.location_visitor.visit(ast)

    def visit_parallel_register(
        self, ast: location.ParallelRegister
    ) -> location.ParallelRegister:
        return self.location_visitor.visit(ast)

    def visit_sequence(self, ast: sequence.Sequence) -> sequence.Sequence:
        return sequence.Sequence(
            {
                coupling_name: self.visit(sub_pulse)
                for coupling_name, sub_pulse in ast.pulses.items()
            }
        )

    def visit_append_sequence(self, ast: sequence.Append) -> sequence.Append:
        return sequence.Append(list(map(self.visit, ast.sequences)))

    def visit_slice_sequence(self, ast: sequence.Slice) -> sequence.Slice:
        return sequence.Slice(
            self.visit(ast.sequence), self.scalar_visitor.emit(ast.interval)
        )

    def visit_named_sequence(
        self, ast: sequence.NamedSequence
    ) -> sequence.NamedSequence:
        return sequence.NamedSequence(self.visit(ast.sequence), ast.name)

    def visit_pulse(self, ast: pulse.Pulse) -> pulse.Pulse:
        return pulse.Pulse(
            {
                field_name: self.visit(sub_field)
                for field_name, sub_field in ast.fields.items()
            }
        )

    def visit_append_pulse(self, ast: pulse.Append) -> pulse.Append:
        return pulse.Append(list(map(self.visit, ast.value)))

    def visit_slice_pulse(self, ast: pulse.Slice) -> pulse.Slice:
        return pulse.Slice(self.visit(ast.pulse), self.scalar_visitor(ast.interval))

    def visit_named_pulse(self, ast: pulse.NamedPulse) -> Any:
        return pulse.NamedPulse(ast.name, self.visit(ast.pulse))

    def visit_field(self, ast: field.Field) -> field.Field:
        return field.Field(
            {self.visit(sm): self.visit(wf) for sm, wf in ast.value.items()}
        )

    def visit_uniform_modulation(self, ast: field.UniformModulation) -> Any:
        return ast

    def visit_location(self, ast: field.Location) -> Any:
        return ast

    def visit_scaled_locations(self, ast: field.ScaledLocations) -> Any:
        return field.ScaledLocations(
            {
                self.visit(loc): self.scalar_visitor.emit(scale)
                for loc, scale in ast.value.items()
            }
        )

    def visit_run_time_vector(
        self, ast: field.RunTimeVector
    ) -> Union[field.RunTimeVector, field.AssignedRunTimeVector]:
        if ast.name in self.mapping:
            return field.AssignedRunTimeVector(ast.name, self.mapping[ast.name])

        return ast

    def visit_assigned_run_time_vector(
        self, ast: field.AssignedRunTimeVector
    ) -> field.AssignedRunTimeVector:
        if ast.name in self.mapping:
            raise ValueError(f"Variable {ast.name} already assigned to {ast.value}.")

        return ast

    def visit_waveform(self, ast: waveform.Waveform) -> waveform.Waveform:
        return self.waveform_visitor.emit(ast)

    def emit(self, ast: analog_circuit.AnalogCircuit) -> analog_circuit.AnalogCircuit:
        return self.visit(ast)
