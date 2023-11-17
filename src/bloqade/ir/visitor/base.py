import bloqade.ir.control.waveform as _waveform
import bloqade.ir.control.field as _field
import bloqade.ir.control.pulse as _pulse
import bloqade.ir.control.sequence as _sequence
import bloqade.ir.location.base as _location
import bloqade.ir.analog_circuit as _analog_circuit
import bloqade.ir.scalar as _scalar
from beartype.typing import Any

from dataclasses import fields

BloqadeNodeTypes = (
    _scalar.Scalar,
    _scalar.Interval,
    _waveform.Waveform,
    _field.FieldExpr,
    _pulse.PulseExpr,
    _sequence.SequenceExpr,
    _location.AtomArrangement,
    _location.ParallelRegister,
    _location.LocationInfo,
    _analog_circuit.AnalogCircuit,
)


# use dataclasses.fields to get the fields of a dataclass
def iter_fields(node: Any) -> Any:
    for field in fields(node):
        yield field, getattr(node, field.name)


class BloqadeIRVisitor:
    # Following the pattern from from python's ast.NodeVisitor

    def visit(self, node: Any) -> Any:
        name = node.__class__.__name__
        module = node.__class__.__module__.split(".")[-1]
        visitor = getattr(self, f"visit_{module}_{name}", self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: Any) -> Any:
        for field, value in iter_fields(node):
            if isinstance(value, BloqadeNodeTypes):
                self.visit(value)
            elif isinstance(value, (list, set, tuple, frozenset)):
                for item in value:
                    if isinstance(item, BloqadeNodeTypes):
                        self.visit(item)
            elif isinstance(value, dict):
                for key, value in value.items():
                    if isinstance(value, BloqadeNodeTypes):
                        self.visit(value)

                    if isinstance(key, BloqadeNodeTypes):
                        self.visit(key)


class BloqadeIRTransformer(BloqadeIRVisitor):
    # Following the pattern from from python's ast.NodeTransformer

    def generic_visit(self, node: Any) -> Any:
        constructor_args = {}
        for field, value in iter_fields(node):
            if isinstance(value, BloqadeNodeTypes):
                new_value = self.visit(value)
            elif isinstance(value, list):
                new_value = [self.visit(item) for item in value]
            elif isinstance(value, set):
                new_value = {self.visit(item) for item in value}
            elif isinstance(value, tuple):
                new_value = tuple(self.visit(item) for item in value)
            elif isinstance(value, dict):  # sometimes keys are also nodes
                new_value = {}
                for key, value in value.items():
                    if isinstance(value, BloqadeNodeTypes):
                        value = self.visit(value)
                    if isinstance(key, BloqadeNodeTypes):
                        key = self.visit(key)
                    new_value[key] = value

            constructor_args[field.name] = value
        # IR nodes are immutable, so we have to use the constructor
        return node.__class__(**constructor_args)
