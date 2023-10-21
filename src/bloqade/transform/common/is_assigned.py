from typing import Any
import bloqade.ir.location as location
import bloqade.ir.control.field as field
import bloqade.ir.control.pulse as pulse
import bloqade.ir.control.sequence as sequence
import bloqade.ir.analog_circuit as analog_circuit
import bloqade.ir.control.waveform as waveform
import bloqade.ir.location.base as location
import bloqade.ir.scalar as scalar
from bloqade.ir.visitor.analog_circuit import AnalogCircuitVisitor
from bloqade.ir.visitor.waveform import WaveformVisitor
from bloqade.ir.visitor.scalar import ScalarVisitor
from bloqade.ir.visitor.location import LocationVisitor



class UnassignedVarsScalar(ScalarVisitor):
    def __init__(self):
        self.unassigned_vars = set()


    def visit_literal(self, _: scalar.Literal) -> Any:
        pass

    def visit_assigned_variable(self, _: scalar.AssignedVariable) -> Any:
        pass

    def visit_variable(self, ast: scalar.Variable) -> Any:
        self.unassigned_vars.add(ast,name)

    def visit_add(self, ast: scalar.Add) -> Any:
        self.visit(ast.lhs)
        self.visit(ast.rhs)

    def visit_div(self, ast: scalar.Div) -> Any:
        self.visit(ast.lhs)
        self.visit(ast.rhs)

    def visit_mul(self, ast: scalar.Mul) -> Any:
        self.visit(ast.lhs)
        self.visit(ast.rhs)

    def visit_min(self, ast: scalar.Min) -> Any:
        for expr in ast.exprs:
            self.visit(expr)

    def visit_max(self, ast: scalar.Max) -> Any:
        for expr in ast.exprs:
            self.visit(expr)

    def visit_negative(self, ast: scalar.Negative) -> Any:
        self.visit(ast.expr)

    def visit_slice(self, ast: scalar.Slice) -> Any:
        self.visit(ast.expr)
        self.visit(ast.interval)

    def visit_interval(self, ast: scalar.Interval) -> Any:
        if ast.start is not None:
            self.visit(ast.start)

        if ast.stop is not None:
            self.visit(ast.stop)

    def scan(self, ast: scalar.Scalar) -> frozenset:
        self.visit(ast)
        return frozenset(self.unassigned_vars)
    
class UnassignedVarsWaveform(WaveformVisitor):
    def __init__(self):
        self.unassigned_vars = set()
        self.scalar_visitor = UnassignedVarsScalar()
        
    def visit_scalar(self, ast: scalar.Scalar) -> Any:
        self.unassigned_vars.update(self.scalar_visitor.scan(ast))

    def visit_constant(self, ast: waveform.Constant) -> Any:
        self.visit_scalar(ast.value)
        self.visit_scalar(ast.duration)

    def visit_linear(self, ast: waveform.Linear) -> Any:
        self.visit_scalar(ast.start)
        self.visit_scalar(ast.stop)
        self.visit_scalar(ast.duration)

    def visit_poly(self, ast: waveform.Poly) -> Any:
        self.visit_scalar(ast.duration)
        list(map(self.visit_scalar, ast.coeffs))

    def visit_python_fn(self, ast: waveform.PythonFn) -> Any:
        self.visit_scalar(ast.duration)
        list(map(self.visit_scalar, ast.args))

    def visit_add(self, ast: Add) -> Any:
        self.visit(ast.left)
        self.visit(ast.right)

    def visit_alligned(self, ast: waveform.AlignedWaveform) -> Any:
        if isinstance(ast.value, scalar.Scalar):
            self.visit_scalar(ast.value)

        self.visit(ast.waveform)

    def visit_append(self, ast: waveform.Append) -> Any:
        list(map(self.visit, ast.waveforms))
        

    def visit_negative(self, ast: waveform.Negative) -> Any:
        self.visit(ast.waveform)

    def visit_record(self, ast: waveform.Record) -> Any:
        self.visit(ast.waveform)
        self.visit_scalar(ast.var)

    def visit_sample(self, ast: waveform.Sample) -> Any:
        self.visit(ast.waveform)
        self.visit_scalar(ast.dt)

    def visit_scale(self, ast: waveform.Scale) -> Any:
        self.visit_scalar(ast.scalar)
        self.visit(ast.waveform)

    def visit_slice(self, ast: waveform.Slice) -> Any:
        self.visit(ast.waveform)
        self.visit(ast.interval)

    def visit_smooth(self, ast: waveform.Smooth) -> Any:
        self.visit_scalar(ast.radius)
        self.visit(ast.waveform)

    def scan(self, ast: waveform.Waveform) -> frozenset:
        self.visit(ast)
        return frozenset(self.unassigned_vars)
    

class UnassignedVarsAnalogCircuit(AnalogCircuitVisitor):
    def __init__(self):
        self.unassigned_scalar_vars = set()
        self.unassigned_vector_vars = set()

        self.scalar_visitor = UnassignedVarsScalar()
        self.waveform_visitor = UnassignedVarsWaveform()

    def visit_scalar(self, ast: scalar.Scalar) -> Any:
        self.unassigned_scalar_vars.update(self.scalar_visitor.scan(ast))

    def visit_waveform(self, ast: waveform.Waveform) -> Any:
        self.unassigned_vector_vars.update(self.waveform_visitor.scan(ast))

    def visit_analog_circuit(self, ast: analog_circuit.AnalogCircuit) -> Any:
        self.visit(ast.register)
        self.visit(ast.sequence)

    def visit_register(self, ast: location.AtomArrangement) -> Any:
        for site_info in ast.enumerate():
            list(map(self.visit_scalar, site_info.position))

    def visit_parallel_register(self, ast: location.ParallelRegister) -> Any:
        self.visit(ast._register)
