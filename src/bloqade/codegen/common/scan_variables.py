from pydantic.dataclasses import dataclass
import bloqade.ir.analog_circuit as analog_circuit
import bloqade.ir.location as location
import bloqade.ir.scalar as scalar
import bloqade.ir.control.waveform as waveform
import bloqade.ir.control.sequence as sequence
import bloqade.ir.control.pulse as pulse
import bloqade.ir.control.field as field

from bloqade.ir.visitor.analog_circuit import AnalogCircuitVisitor
from bloqade.ir.visitor.location import LocationVisitor
from bloqade.ir.visitor.waveform import WaveformVisitor
from bloqade.ir.visitor.scalar import ScalarVisitor
from beartype.typing import Set, Any, FrozenSet


@dataclass(frozen=True)
class ScanVariableResults:
    scalar_vars: FrozenSet[str]
    vector_vars: FrozenSet[str]


class ScanVariablesScalar(ScalarVisitor):
    def __init__(self):
        self.vars = set()

    def visit_literal(self, ast: scalar.Literal) -> Any:
        pass

    def visit_assigned_variable(self, ast: scalar.AssignedVariable) -> Any:
        self.vars.add(ast.name)

    def visit_variable(self, ast: scalar.Variable) -> Any:
        self.vars.add(ast.name)

    def visit_add(self, ast: scalar.Add) -> Any:
        self.visit(ast.lhs)
        self.visit(ast.rhs)

    def visit_mul(self, ast: scalar.Mul) -> Any:
        self.visit(ast.lhs)
        self.visit(ast.rhs)

    def visit_div(self, ast: scalar.Div) -> Any:
        self.visit(ast.lhs)
        self.visit(ast.rhs)

    def visit_interval(self, ast: scalar.Interval) -> Any:
        self.visit(ast.start)
        self.visit(ast.stop)

    def visit_slice(self, ast: scalar.Slice) -> Any:
        self.visit(ast.expr)
        self.visit(ast.interval)

    def visit_max(self, ast: scalar.Max) -> Any:
        list(map(self.visit, ast.exprs))

    def visit_min(self, ast: scalar.Min) -> Any:
        list(map(self.visit, ast.exprs))

    def visit_negative(self, ast: scalar.Negative) -> Any:
        self.visit(ast.expr)

    def emit(self, ast: scalar.Scalar) -> Set[str]:
        self.visit(ast)
        return self.vars


class ScanVariablesWaveform(WaveformVisitor):
    def __init__(self):
        self.vars = set()
        self.scalar_visitor = ScanVariablesScalar()

    def visit_constant(self, ast: waveform.Constant) -> Any:
        self.vars = self.vars.union(self.scalar_visitor.emit(ast.value))
        self.vars = self.vars.union(self.scalar_visitor.emit(ast.duration))

    def visit_linear(self, ast: waveform.Linear) -> Any:
        self.vars = self.vars.union(self.scalar_visitor.emit(ast.start))
        self.vars = self.vars.union(self.scalar_visitor.emit(ast.stop))
        self.vars = self.vars.union(self.scalar_visitor.emit(ast.duration))

    def visit_poly(self, ast: waveform.Poly) -> Any:
        for coeff in ast.coeffs:
            self.vars = self.vars.union(self.scalar_visitor.emit(coeff))
        self.vars = self.vars.union(self.scalar_visitor.emit(ast.duration))

    def visit_python_fn(self, ast: waveform.PythonFn) -> Any:
        self.vars = self.vars.union(self.scalar_visitor.emit(ast.duration))
        for parameter in ast.parameters:
            self.vars = self.vars.union(self.scalar_visitor.emit(parameter))

    def visit_negative(self, ast: waveform.Negative) -> Any:
        self.visit(ast.waveform)

    def visit_record(self, ast: waveform.Record):
        self.visit(ast.waveform)
        self.vars.add(ast.var.name)

    def visit_add(self, ast: waveform.Add) -> Any:
        self.visit(ast.left)
        self.visit(ast.right)

    def visit_scale(self, ast: waveform.Scale) -> Any:
        self.visit(ast.waveform)
        self.vars = self.vars.union(self.scalar_visitor.emit(ast.scalar))

    def visit_alligned(self, ast: waveform.AlignedWaveform) -> Any:
        self.visit(ast.waveform)
        if isinstance(ast.value, scalar.Scalar):
            self.vars = self.vars.union(self.scalar_visitor.emit(ast.value))

    def visit_sample(self, ast: waveform.Sample) -> Any:
        self.vars = self.vars.union(self.scalar_visitor.emit(ast.dt))
        self.visit(ast.waveform)

    def visit_append(self, ast: waveform.Append) -> Any:
        list(map(self.visit, ast.waveforms))

    def visit_slice(self, ast: waveform.Slice) -> Any:
        self.vars = self.vars.union(self.scalar_visitor.emit(ast.interval))
        self.visit(ast.waveform)

    def visit_smooth(self, ast: waveform.Smooth) -> Any:
        self.visit(ast.waveform)
        self.vars = self.vars.union(self.scalar_visitor.emit(ast.radius))

    def emit(self, ast: waveform.Waveform) -> Set[str]:
        self.visit(ast)
        return self.vars


class ScanVariablesLocation(LocationVisitor):
    def __init__(self):
        self.vars = set()
        self.scalar_visitor = ScanVariablesScalar()

    def visit_bravais(self, ast: location.BoundedBravais) -> Any:
        self.vars = self.vars.union(self.scalar_visitor.emit(ast.lattice_spacing))

    def visit_chain(self, ast: location.Chain) -> Any:
        self.visit_bravais(ast)

    def visit_honeycomb(self, ast: location.Honeycomb) -> Any:
        self.visit_bravais(ast)

    def visit_kagome(self, ast: location.Kagome) -> Any:
        self.visit_bravais(ast)

    def visit_lieb(self, ast: location.Lieb) -> Any:
        self.visit_bravais(ast)

    def visit_square(self, ast: location.Square) -> Any:
        self.visit_bravais(ast)

    def visit_triangular(self, ast: location.Triangular) -> Any:
        self.visit_bravais(ast)

    def visit_rectangular(self, ast: location.Rectangular) -> Any:
        self.scalar_visitor.emit(ast.lattice_spacing_x)
        self.scalar_visitor.emit(ast.lattice_spacing_y)

    def visit_list_of_locations(self, ast: location.ListOfLocations) -> Any:
        for loc in ast.location_list:
            self.visit(loc)

    def visit_location_info(self, ast: location.LocationInfo) -> Any:
        for coord in ast.position:
            self.vars = self.vars.union(self.scalar_visitor.emit(coord))

    def visit_parallel_register(self, ast: location.ParallelRegister) -> Any:
        self.visit(ast._register)
        self.vars = self.vars.union(self.scalar_visitor.emit(ast._cluster_spacing))

    def emit(self, ast: location.AtomArrangement) -> Set[str]:
        self.visit(ast)
        return self.vars


class ScanVariablesAnalogCircuit(AnalogCircuitVisitor):
    def __init__(self):
        self.scalar_vars = set()
        self.vector_vars = set()
        self.waveform_visitor = ScanVariablesWaveform()
        self.scalar_visitor = ScanVariablesScalar()
        self.location_visitor = ScanVariablesLocation()

    def visit_uniform_modulation(self, ast: field.UniformModulation) -> Any:
        pass

    def visit_scaled_locations(self, ast: field.ScaledLocations) -> Any:
        for value in ast.value.values():
            self.scalar_vars = self.scalar_vars.union(self.scalar_visitor.emit(value))

    def visit_run_time_vector(self, ast: field.RunTimeVector) -> Any:
        self.vector_vars.add(ast.name)

    def visit_assigned_run_time_vector(self, ast: field.AssignedRunTimeVector) -> Any:
        self.vector_vars.add(ast.name)

    def visit_field(self, ast: field.Field) -> Any:
        list(map(self.visit, ast.value.keys()))
        for value in ast.value.values():
            self.visit(value)

    def visit_pulse(self, ast: pulse.Pulse) -> Any:
        list(map(self.visit, ast.fields.values()))

    def visit_append_pulse(self, ast: pulse.Append) -> Any:
        list(map(self.visit, ast.value))

    def visit_slice_pulse(self, ast: pulse.Slice) -> Any:
        self.scalar_vars = self.scalar_vars.union(
            self.scalar_visitor.emit(ast.interval)
        )
        self.visit(ast.pulse)

    def visit_named_pulse(self, ast: pulse.NamedPulse) -> Any:
        self.visit(ast.pulse)

    def visit_sequence(self, ast: sequence.Sequence) -> Any:
        list(map(self.visit, ast.pulses.values()))

    def visit_append_sequence(self, ast: sequence.Append) -> Any:
        list(map(self.visit, ast.value))

    def visit_slice_sequence(self, ast: sequence.Slice) -> Any:
        self.scalar_vars = self.scalar_vars.union(
            self.scalar_visitor.emit(ast.interval)
        )
        self.visit(ast.sequence)

    def visit_named_sequence(self, ast: sequence.NamedSequence) -> Any:
        self.visit(ast.sequence)

    def visit_waveform(self, ast: waveform.Waveform) -> Any:
        self.scalar_vars = self.scalar_vars.union(self.waveform_visitor.emit(ast))

    def visit_register(self, ast: location.AtomArrangement) -> Any:
        self.scalar_vars = self.scalar_vars.union(self.location_visitor.emit(ast))

    def visit_parallel_register(self, ast: location.ParallelRegister) -> Any:
        self.scalar_vars = self.scalar_vars.union(self.location_visitor.emit(ast))

    def visit_analog_circuit(self, ast: analog_circuit.AnalogCircuit) -> Any:
        print(type(ast.register))
        self.visit(ast.register)
        self.visit(ast.sequence)

    def emit(self, ast: analog_circuit.AnalogCircuit) -> ScanVariableResults:
        self.visit(ast)
        return ScanVariableResults(self.scalar_vars, self.vector_vars)
