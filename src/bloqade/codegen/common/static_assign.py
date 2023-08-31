from bloqade.ir.location.base import AtomArrangement, ParallelRegister, LocationInfo
from bloqade.ir.visitor.analog_circuit import AnalogCircuitVisitor
from bloqade.ir.visitor.waveform import WaveformVisitor
from bloqade.ir.visitor.scalar import ScalarVisitor
import bloqade.ir.analog_circuit as analog_circuit

# import bloqade.ir.location as location
import bloqade.ir.control.sequence as sequence
import bloqade.ir.control.pulse as pulse
import bloqade.ir.control.field as field
import bloqade.ir.control.waveform as waveform
import bloqade.ir.scalar as scalar
import bloqade.ir.location as location
import numbers
from typing import Any, Dict
from decimal import Decimal


class StaticAssignScalar(ScalarVisitor):
    def __init__(self, mapping: Dict[str, Decimal]):
        self.mapping = dict(mapping)

    def visit_literal(self, ast: scalar.Literal) -> scalar.Scalar:
        return ast

    def visit_variable(self, ast: scalar.Variable) -> scalar.AssignedVariable:
        if ast.name in self.mapping:
            return scalar.AssignedVariable(ast.name, self.mapping[ast.name])

        return ast

    def visit_assigned_variable(self, ast: scalar.Variable) -> scalar.AssignedVariable:
        if ast.name in self.mapping:
            raise ValueError(f"Variable {ast.name} is already assigned.")

        return ast

    def visit_negative(self, ast: scalar.Negative) -> scalar.Negative:
        return scalar.Negative(self.visit(ast.expr))

    def visit_add(self, ast: scalar.Add) -> scalar.Add:
        return scalar.Add(self.visit(ast.lhs), self.visit(ast.rhs))

    def visit_div(self, ast: scalar.Div) -> scalar.Div:
        return scalar.Div(self.visit(ast.lhs), self.visit(ast.rhs))

    def visit_mul(self, ast: scalar.Mul) -> scalar.Mul:
        return scalar.Mul(self.visit(ast.lhs), self.visit(ast.rhs))

    def visit_min(self, ast: scalar.Min) -> scalar.Min:
        return scalar.Min(frozenset(list(map(self.visit, ast.scalars))))

    def visit_max(self, ast: scalar.Min) -> scalar.Min:
        return scalar.Max(frozenset(list(map(self.visit, ast.scalars))))

    def emit(self, ast: scalar.Scalar) -> scalar.Scalar:
        # canonicalize at the end
        return scalar.Scalar.canonicalize(self.visit(ast))


class StaticAssignWaveform(WaveformVisitor):
    def __init__(self, mapping: Dict[str, numbers.Real]):
        self.scalar_visitor = StaticAssignScalar(mapping)
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
        new_ast = waveform.PythonFn(ast.fn, self.scalar_visitor.visit(ast.duration))
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
        return waveform.Record(self.visit(ast.waveform), ast.var)

    def visit_sample(self, ast: waveform.Sample) -> Any:
        dt = self.scalar_visitor.emit(ast.dt)
        return waveform.Sample(self.visit(ast.waveform), ast.interpolation, dt)

    def visit_scale(self, ast: waveform.Scale) -> Any:
        scalar = self.scalar_visitor.visit(ast.scalar)
        return waveform.Scale(scalar, self.visit(ast.waveform))

    def visit_slice(self, ast: waveform.Slice) -> Any:
        start = ast.interval.start
        stop = ast.interval.stop

        if start is not None:
            start = self.scalar_visitor.emit(start)

        if stop is not None:
            stop = self.scalar_visitor.emit(stop)

        return waveform.Slice(self.visit(ast.waveform), scalar.Interval(start, stop))

    def emit(self, ast: waveform.Waveform) -> waveform.Waveform:
        return self.visit(ast)


class AssignAnalogCircuit(AnalogCircuitVisitor):
    def __init__(self, mapping: Dict[str, numbers.Real]):
        self.waveform_visitor = StaticAssignWaveform(mapping)
        self.scalar_visitor = StaticAssignScalar(mapping)
        self.mapping = dict(mapping)

    def visit_parallel_register(self, ast: ParallelRegister) -> Any:
        return ParallelRegister(
            self.visit(ast._register), self.scalar_visitor.emit(ast._cluster_spacing)
        )

    def visit_register(self, ast: AtomArrangement) -> Any:
        match ast:
            case location.ListOfLocations(location_list):
                # implement static assign on location_list
                new_loc_list = []
                for loc in location_list:
                    new_loc_list.append(
                        LocationInfo(
                            (
                                self.scalar_visitor.emit(loc.position[0]),
                                self.scalar_visitor.emit(loc.position[1]),
                            ),
                            loc.filling,
                        )
                    )

                return location.ListOfLocations(new_loc_list)

            case location.Rectangular(shape, lattice_spacing, ratio):
                ls_x = self.scalar_visitor.emit(lattice_spacing)
                ls_y = self.scalar_visitor.emit(ratio) * ls_x
                return location.Rectangular(shape[0], shape[1], ls_x, ls_y)

            case location.Square(shape, lattice_spacing):
                return location.Square(
                    shape[0], lattice_spacing=self.scalar_visitor.emit(lattice_spacing)
                )

            case location.Kagome(shape, lattice_spacing):
                return location.Kagome(
                    shape[0], lattice_spacing=self.scalar_visitor.emit(lattice_spacing)
                )

            case location.Chain(shape, lattice_spacing):
                return location.Chain(
                    shape[0], lattice_spacing=self.scalar_visitor.emit(lattice_spacing)
                )

            case location.Triangular(shape, lattice_spacing):
                return location.Triangular(
                    shape[0], lattice_spacing=self.scalar_visitor.emit(lattice_spacing)
                )

            case location.Honeycomb(shape, lattice_spacing):
                return location.Honeycomb(
                    shape[0], lattice_spacing=self.scalar_visitor.emit(lattice_spacing)
                )

            case location.Lieb(shape, lattice_spacing):
                return location.Lieb(
                    shape[0], lattice_spacing=self.scalar_visitor.emit(lattice_spacing)
                )

        raise NotImplementedError

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
                return sequence.Slice(
                    self.visit(sub_sequence), self.scalar_visitor.emit(interval)
                )
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
                return pulse.Slice(
                    self.visit(sub_pulse), self.scalar_visitor.emit(interval)
                )
            case pulse.NamedPulse(name, sub_pulse):
                return pulse.NamedPulse(name, self.visit(sub_pulse))

    def visit_field(self, ast: field.Field) -> field.Field:
        return field.Field(
            {self.visit(sm): self.visit(wf) for sm, wf in ast.value.items()}
        )

    def visit_spatial_modulation(
        self, ast: field.SpatialModulation
    ) -> field.SpatialModulation:
        match ast:
            case field.Uniform:
                return field.Uniform
            case field.RunTimeVector(name):
                return field.RunTimeVector(name)
            case field.ScaledLocations(locations):
                return field.ScaledLocations(
                    {
                        loc: self.scalar_visitor.emit(scale)
                        for loc, scale in locations.items()
                    }
                )

    def visit_waveform(self, ast: waveform.Waveform) -> waveform.Waveform:
        return self.waveform_visitor.emit(ast)

    def visit_analog_circuit(
        self, ast: analog_circuit.AnalogCircuit
    ) -> analog_circuit.AnalogCircuit:
        return analog_circuit.AnalogCircuit(
            self.visit(ast.register),
            self.visit(ast.sequence),
        )
