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
from beartype.typing import Any, FrozenSet


@dataclass(frozen=True)
class ScanVariableResults:
    scalar_vars: FrozenSet[str]
    vector_vars: FrozenSet[str]
    assigned_scalar_vars: FrozenSet[str]
    assigned_vector_vars: FrozenSet[str]

    @property
    def is_assigned(self) -> bool:
        return len(self.scalar_vars) == 0 or len(self.vector_vars) == 0


class ScanVariablesScalar(ScalarVisitor):
    def __init__(self):
        self.scalar_vars = set()
        self.assigned_scalar_vars = set()

    def visit_literal(self, ast: scalar.Literal) -> Any:
        pass

    def visit_assigned_variable(self, ast: scalar.AssignedVariable) -> Any:
        self.assigned_scalar_vars.add(ast.name)

    def visit_variable(self, ast: scalar.Variable) -> Any:
        self.scalar_vars.add(ast.name)

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
        if ast.start is not None:
            self.visit(ast.start)

        if ast.stop is not None:
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

    def scan(self, ast: scalar.Scalar) -> ScanVariableResults:
        self.visit(ast)
        return ScanVariableResults(
            self.scalar_vars, self.assigned_scalar_vars, set(), set()
        )


class ScanVariablesWaveform(WaveformVisitor):
    def __init__(self):
        self.scalar_vars = set()
        self.assigned_scalar_vars = set()
        self.scalar_visitor = ScanVariablesScalar()

    def update(self, other: ScanVariableResults):
        self.scalar_vars = self.scalar_vars.union(other.scalar_vars)
        self.assigned_scalar_vars = self.assigned_scalar_vars.union(
            other.assigned_scalar_vars
        )

    def visit_constant(self, ast: waveform.Constant) -> Any:
        self.update(self.scalar_visitor.scan(ast.value))
        self.update(self.scalar_visitor.scan(ast.duration))

    def visit_linear(self, ast: waveform.Linear) -> Any:
        self.update(self.scalar_visitor.scan(ast.start))
        self.update(self.scalar_visitor.scan(ast.stop))
        self.update(self.scalar_visitor.scan(ast.duration))

    def visit_poly(self, ast: waveform.Poly) -> Any:
        for coeff in ast.coeffs:
            self.update(self.scalar_visitor.scan(coeff))
        self.update(self.scalar_visitor.scan(ast.duration))

    def visit_python_fn(self, ast: waveform.PythonFn) -> Any:
        self.update(self.scalar_visitor.scan(ast.duration))
        for parameter in ast.parameters:
            self.update(self.scalar_visitor.scan(parameter))

    def visit_negative(self, ast: waveform.Negative) -> Any:
        self.visit(ast.waveform)

    def visit_record(self, ast: waveform.Record):
        self.visit(ast.waveform)
        self.scalar_vars.add(ast.var.name)

    def visit_add(self, ast: waveform.Add) -> Any:
        self.visit(ast.left)
        self.visit(ast.right)

    def visit_scale(self, ast: waveform.Scale) -> Any:
        self.visit(ast.waveform)
        self.update(self.scalar_visitor.scan(ast.scalar))

    def visit_alligned(self, ast: waveform.AlignedWaveform) -> Any:
        self.visit(ast.waveform)
        if isinstance(ast.value, scalar.Scalar):
            self.update(self.scalar_visitor.scan(ast.value))

    def visit_sample(self, ast: waveform.Sample) -> Any:
        self.update(self.scalar_visitor.scan(ast.dt))
        self.visit(ast.waveform)

    def visit_append(self, ast: waveform.Append) -> Any:
        list(map(self.visit, ast.waveforms))

    def visit_slice(self, ast: waveform.Slice) -> Any:
        self.update(self.scalar_visitor.scan(ast.interval))
        self.visit(ast.waveform)

    def visit_smooth(self, ast: waveform.Smooth) -> Any:
        self.visit(ast.waveform)
        self.update(self.scalar_visitor.scan(ast.radius))

    def emit(self, ast: waveform.Waveform) -> ScanVariableResults:
        self.visit(ast)
        return ScanVariableResults(
            self.scalar_vars, set(), self.assigned_scalar_vars, set()
        )


class ScanVariablesLocation(LocationVisitor):
    def __init__(self):
        self.scalar_vars = set()
        self.assigned_scalar_vars = set()
        self.scalar_visitor = ScanVariablesScalar()

    def update(self, results: ScanVariableResults):
        self.scalar_vars = self.scalar_vars.union(results.scalar_vars)
        self.assigned_scalar_vars = self.assigned_scalar_vars.union(
            results.assigned_scalar_vars
        )

    def visit_bravais(self, ast: location.BoundedBravais) -> Any:
        self.update(self.scalar_visitor.scan(ast.lattice_spacing))

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
        self.update(self.scalar_visitor.scan(ast.lattice_spacing_x))
        self.update(self.scalar_visitor.scan(ast.lattice_spacing_y))

    def visit_list_of_locations(self, ast: location.ListOfLocations) -> Any:
        for loc in ast.location_list:
            self.visit(loc)

    def visit_location_info(self, ast: location.LocationInfo) -> Any:
        for coord in ast.position:
            self.update(self.scalar_visitor.scan(coord))

    def visit_parallel_register(self, ast: location.ParallelRegister) -> Any:
        self.visit(ast._register)
        self.update(self.scalar_visitor.scan(ast._cluster_spacing))

    def scan(self, ast: location.AtomArrangement) -> ScanVariableResults:
        self.visit(ast)
        return ScanVariableResults(
            self.scalar_vars, set(), self.assigned_scalar_vars, set()
        )


class ScanVariablesAnalogCircuit(AnalogCircuitVisitor):
    def __init__(self):
        self.scalar_vars = set()
        self.vector_vars = set()
        self.assigned_scalar_vars = set()
        self.assigned_vector_vars = set()
        self.waveform_visitor = ScanVariablesWaveform()
        self.scalar_visitor = ScanVariablesScalar()
        self.location_visitor = ScanVariablesLocation()

    def update(self, other: ScanVariableResults):
        self.scalar_vars = self.scalar_vars.union(other.scalar_vars)
        self.vector_vars = self.vector_vars.union(other.vector_vars)
        self.assigned_scalar_vars = self.assigned_scalar_vars.union(
            other.assigned_scalar_vars
        )
        self.assigned_vector_vars = self.assigned_vector_vars.union(
            other.assigned_vector_vars
        )

    def visit_uniform_modulation(self, ast: field.UniformModulation) -> Any:
        pass

    def visit_scaled_locations(self, ast: field.ScaledLocations) -> Any:
        for value in ast.value.values():
            self.update(self.scalar_visitor.scan(value))

    def visit_run_time_vector(self, ast: field.RunTimeVector) -> Any:
        self.vector_vars.add(ast.name)

    def visit_assigned_run_time_vector(self, ast: field.AssignedRunTimeVector) -> Any:
        self.assigned_vector_vars.add(ast.name)

    def visit_field(self, ast: field.Field) -> Any:
        list(map(self.visit, ast.drives.keys()))
        list(map(self.visit, ast.drives.values()))

    def visit_pulse(self, ast: pulse.Pulse) -> Any:
        list(map(self.visit, ast.fields.values()))

    def visit_append_pulse(self, ast: pulse.Append) -> Any:
        list(map(self.visit, ast.pulses))

    def visit_slice_pulse(self, ast: pulse.Slice) -> Any:
        self.update(self.scalar_visitor.scan(ast.interval))
        self.visit(ast.pulse)

    def visit_named_pulse(self, ast: pulse.NamedPulse) -> Any:
        self.visit(ast.pulse)

    def visit_sequence(self, ast: sequence.Sequence) -> Any:
        list(map(self.visit, ast.pulses.values()))

    def visit_append_sequence(self, ast: sequence.Append) -> Any:
        list(map(self.visit, ast.sequences))

    def visit_slice_sequence(self, ast: sequence.Slice) -> Any:
        self.update(self.scalar_visitor.scan(ast.interval))
        self.visit(ast.sequence)

    def visit_named_sequence(self, ast: sequence.NamedSequence) -> Any:
        self.visit(ast.sequence)

    def visit_waveform(self, ast: waveform.Waveform) -> Any:
        self.update(self.waveform_visitor.emit(ast))

    def visit_register(self, ast: location.AtomArrangement) -> Any:
        self.update(self.location_visitor.scan(ast))

    def visit_parallel_register(self, ast: location.ParallelRegister) -> Any:
        self.update(self.location_visitor.scan(ast))

    def visit_analog_circuit(self, ast: analog_circuit.AnalogCircuit) -> Any:
        self.visit(ast.register)
        self.visit(ast.sequence)

    def scan(self, ast: analog_circuit.AnalogCircuit) -> ScanVariableResults:
        self.visit(ast)
        return ScanVariableResults(
            self.scalar_vars,
            self.vector_vars,
            self.assigned_scalar_vars,
            self.assigned_vector_vars,
        )
