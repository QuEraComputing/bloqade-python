import bloqade.ir.location as location
import bloqade.ir.control.sequence as sequence
import bloqade.ir.control.pulse as pulse
import bloqade.ir.control.field as field
import bloqade.ir.analog_circuit as analog_circuit
import bloqade.ir.control.waveform as waveform
from bloqade.ir.location import (
    Chain,
    Honeycomb,
    Kagome,
    Lieb,
    ListOfLocations,
    Rectangular,
    Square,
    Triangular,
)
from bloqade.ir.location.base import AtomArrangement, LocationInfo, ParallelRegister
import bloqade.ir.scalar as scalar

from bloqade.ir.visitor.analog_circuit import AnalogCircuitVisitor
from bloqade.ir.visitor.location import LocationVisitor
from bloqade.ir.visitor.waveform import WaveformVisitor
from bloqade.ir.visitor.scalar import ScalarVisitor

import json

from typing import Any, Dict


class ScalarSerilaizer(ScalarVisitor):
    def visit_literal(self, ast: scalar.Literal) -> Dict[str, Dict[str, str]]:
        return {"literal": {"value": str(ast.value)}}

    def visit_variable(self, ast: scalar.Variable) -> Dict[str, Dict[str, str]]:
        return {"variable": {"name": ast.name}}

    def visit_assigned_variable(self, ast: scalar.AssignedVariable) -> Dict[str, Any]:
        return {
            "assigned_variable": {
                "name": ast.name,
                "value": str(ast.value),
            }
        }

    def visit_negative(self, ast: scalar.Negative) -> Dict[str, Any]:
        return {"negative": {"expr": self.visit(ast.expr)}}

    def visit_add(self, ast: scalar.Add) -> Dict[str, Any]:
        return {"add": {"lhs": self.visit(ast.lhs), "rhs": self.visit(ast.rhs)}}

    def visit_mul(self, ast: scalar.Mul) -> Dict[str, Any]:
        return {"mul": {"lhs": self.visit(ast.lhs), "rhs": self.visit(ast.rhs)}}

    def visit_div(self, ast: scalar.Max) -> Dict[str, Any]:
        return {"div": {"lhs": self.visit(ast.lhs), "rhs": self.visit(ast.rhs)}}

    def visit_min(self, ast: scalar.Min) -> Dict[str, Any]:
        return {"min": {"exprs": list(map(self.visit, ast.exprs))}}

    def visit_max(self, ast: scalar.Min) -> Dict[str, Any]:
        return {"max": {"exprs": list(map(self.visit, ast.exprs))}}

    def visit_slice(self, ast: scalar.Slice):
        return {
            "slice_scalar": {
                "expr": self.visit(ast.expr),
                "interval": self.visit(ast.interval),
            }
        }

    def visit_interval(self, ast: scalar.Interval) -> Dict[str, Any]:
        return {
            "interval": {
                "start": self.visit(ast.start) if ast.start is not None else None,
                "stop": self.visit(ast.stop) if ast.stop is not None else None,
            }
        }

    def default(self, obj: Any) -> Dict[str, Any]:
        if isinstance(obj, scalar.Scalar):
            return self.visit(obj)

        return super().default(obj)


class WaveformSerializer(WaveformVisitor):
    def __init__(self):
        self.scalar_encoder = ScalarSerilaizer()

    def visit_constant(self, ast: waveform.Constant) -> Dict[str, Any]:
        return {
            "constant": {
                "value": self.scalar_encoder.visit(ast.value),
                "duration": self.scalar_encoder.visit(ast.duration),
            }
        }

    def visit_linear(self, ast: waveform.Linear) -> Dict[str, Any]:
        return {
            "linear": {
                "start": self.scalar_encoder.visit(ast.start),
                "stop": self.scalar_encoder.visit(ast.stop),
                "duration": self.scalar_encoder.visit(ast.duration),
            }
        }

    def visit_poly(self, ast: waveform.Poly) -> Dict[str, Any]:
        return {
            "poly": {
                "coeffs": list(map(self.scalar_encoder.visit, ast.coeffs)),
                "duration": self.scalar_encoder.visit(ast.duration),
            }
        }

    def visit_python_fn(self, ast: waveform.PythonFn) -> Dict[str, Any]:
        raise ValueError("Bloqade does not support serialization of Python code.")

    def visit_negative(self, ast: waveform.Negative) -> Dict[str, Any]:
        return {"negative_waveform": {"waveform": self.visit(ast.waveform)}}

    def visit_add(self, ast: waveform.Add) -> Dict[str, Any]:
        return {
            "add_waveform": {
                "left": self.visit(ast.left),
                "right": self.visit(ast.right),
            }
        }

    def visit_scale(self, ast: waveform.Scale) -> Dict[str, Any]:
        return {
            "scale": {
                "waveform": self.visit(ast.waveform),
                "scalar": self.scalar_encoder.visit(ast.scalar),
            }
        }

    def visit_slice(self, ast: waveform.Slice) -> Dict[str, Any]:
        return {
            "slice_waveform": {
                "waveform": self.visit(ast.waveform),
                "interval": self.scalar_encoder.visit(ast.interval),
            }
        }

    def visit_sample(self, ast: waveform.Sample) -> Dict[str, Any]:
        return {
            "sample": {
                "waveform": self.visit(ast.waveform),
                "dt": self.scalar_encoder.visit(ast.dt),
                "interpolation": ast.interpolation.value,
            }
        }

    def visit_append(self, ast: waveform.Append) -> Dict[str, Any]:
        return {"append_waveform": {"waveforms": list(map(self.visit, ast.waveforms))}}

    def visit_record(self, ast: waveform.Record) -> Dict[str, Any]:
        return {
            "record": {
                "var": self.scalar_encoder(ast.var),
                "waveform": self.visit(ast.waveform),
            }
        }

    def visit_smooth(self, ast: waveform.Smooth) -> Dict[str, Any]:
        return {
            "smooth": {
                "waveform": self.visit(ast.waveform),
                "radius": self.scalar_encoder.visit(ast.radius),
                "kernel": type(ast.kernel).__name__,
            }
        }

    def visit_alligned(self, ast: waveform.AlignedWaveform) -> Dict[str, Any]:
        if isinstance(ast.value, scalar.Scalar):
            value = self.scalar_encoder.visit(ast.value)
        else:
            value = ast.value.value
        return {
            "alligned": {
                "waveform": self.visit(ast.waveform),
                "allignment": self.scalar_encoder.visit(ast.allignment),
                "value": value,
            }
        }

    def default(self, obj: Any) -> Dict[str, Any]:
        if isinstance(obj, waveform.Waveform):
            return self.visit(obj)

        return super().default(obj)


class LocationSerializer(LocationVisitor):
    def __init__(self):
        self.scalar_serializer = ScalarSerilaizer()

    def visit_location_info(self, info: LocationInfo) -> Any:
        return {
            "location_info": {
                "position": list(map(self.scalar_serializer.visit, info.position)),
                "filled": bool(info.filling.value),
            }
        }

    def visit_chain(self, ast: Chain) -> Any:
        return {
            "chain": {
                "lattice_spacing": self.scalar_serializer.visit(ast.lattice_spacing),
                "L": ast.shape[0],
                "vertical_chain": ast.vertical,
            }
        }

    def visit_honeycomb(self, ast: Honeycomb) -> Any:
        return {
            "honeycomb": {
                "lattice_spacing": self.scalar_serializer.visit(ast.lattice_spacing),
                "L1": ast.shape[0],
                "L2": ast.shape[1],
            }
        }

    def visit_kagome(self, ast: Kagome) -> Any:
        return {
            "kagome": {
                "lattice_spacing": self.scalar_serializer.visit(ast.lattice_spacing),
                "L1": ast.shape[0],
                "L2": ast.shape[1],
            }
        }

    def visit_lieb(self, ast: Lieb) -> Any:
        return {
            "lieb": {
                "lattice_spacing": self.scalar_serializer.visit(ast.lattice_spacing),
                "L1": ast.shape[0],
                "L2": ast.shape[1],
            }
        }

    def visit_list_of_locations(self, ast: ListOfLocations) -> Any:
        return {
            "list_of_locations": {
                "location_list": list(map(self.visit, ast.location_list))
            }
        }

    def visit_rectangular(self, ast: Rectangular) -> Any:
        return {
            "rectangular": {
                "lattice_spacing_x": self.scalar_serializer.visit(
                    ast.lattice_spacing_x
                ),
                "lattice_spacing_y": self.scalar_serializer.visit(
                    ast.lattice_spacing_y
                ),
                "width": ast.shape[0],
                "height": ast.shape[1],
            }
        }

    def visit_square(self, ast: Square) -> Any:
        return {
            "square": {
                "lattice_spacing": self.visit(
                    self.scalar_serializer.visit(ast.lattice_spacing)
                ),
                "L1": ast.shape[0],
                "L2": ast.shape[1],
            }
        }

    def visit_triangular(self, ast: Triangular) -> Any:
        return {
            "triangular": {
                "lattice_spacing": self.scalar_serializer.visit(ast.lattice_spacing),
                "L1": ast.shape[0],
                "L2": ast.shape[1],
            }
        }

    def visit_parallel_register(self, ast: location.ParallelRegister) -> Any:
        return {
            "parallel_register": {
                "register": self.visit(ast._register),
                "cluster_spacing": self.visit(ast._cluster_spacing),
            }
        }


class AnalogCircuitSerializer(AnalogCircuitVisitor):
    def __init__(self) -> None:
        self.waveform_serializer = WaveformSerializer()
        self.scalar_serializer = ScalarSerilaizer()
        self.location_serializer = LocationSerializer()

    def visit_register(self, ast: AtomArrangement) -> Any:
        return self.location_serializer.visit(ast)

    def visit_parallel_register(self, ast: ParallelRegister) -> Any:
        return self.location_serializer.visit(ast)

    def visit_sequence(self, ast: sequence.Sequence) -> Dict[str, Any]:
        object_to_str = {
            sequence.rydberg: "rydberg",
            sequence.hyperfine: "hyperfine",
        }
        return {
            "sequence": {
                "pulses": {
                    object_to_str[k]: self.visit(v) for k, v in ast.pulses.items()
                }
            }
        }

    def visit_named_sequence(self, ast: sequence.NamedSequence) -> Dict[str, Any]:
        return {
            "named_sequence": {
                "name": ast.name,
                "sub_sequence": self.visit(ast.sub_sequence),
            }
        }

    def visit_append_sequence(self, ast: sequence.Append) -> Dict[str, Any]:
        return {
            "append_sequence": {"sequences": [self.visit(s) for s in ast.sequences]}
        }

    def visit_slice_sequence(self, ast: sequence.Slice) -> Dict[str, Any]:
        return {
            "slice_sequence": {
                "sequence": self.visit(ast.sequence),
                "interval": self.scalar_serializer.visit(ast.interval),
            }
        }

    def visit_pulse(self, ast: pulse.Pulse):
        object_map_str = {
            pulse.detuning: "detuning",
            pulse.rabi.amplitude: "rabi_frequency_amplitude",
            pulse.rabi.phase: "rabi_frequency_phase",
        }
        return {
            "pulse": {
                "fields": {
                    object_map_str[k]: self.visit(v) for k, v in ast.fields.items()
                }
            }
        }

    def visit_append_pulse(self, ast: pulse.Append) -> Dict[str, Any]:
        return {"append_pulse": {"pulses": [self.visit(p) for p in ast.pulses]}}

    def visit_named_pulse(self, ast: pulse.NamedPulse) -> Dict[str, Any]:
        return {
            "named_pulse": {"name": ast.name, "sub_pulse": self.visit(ast.sub_pulse)}
        }

    def visit_slice_pulse(self, ast: pulse.Slice) -> Dict[str, Any]:
        return {
            "slice_pulse": {
                "pulse": self.visit(ast.sub_pulse),
                "interval": self.scalar_serializer.visit(ast.interval),
            }
        }

    def visit_location(self, ast: field.Location) -> Dict[str, Any]:
        return {"location": {"label": ast.label}}

    def visit_scaled_locations(self, ast: field.ScaledLocations) -> Dict[str, Any]:
        return {
            "scaled_locations": [(self.visit(k), self.visit(v)) for k, v in ast.items()]
        }

    def visit_uniform(self, ast: field.Uniform) -> Dict[str, Any]:
        return {"uniform": {}}

    def visit_run_time_vector(self, ast: field.RunTimeVector) -> Dict[str, Any]:
        return {"run_time_vector": {"name": ast.name}}

    def visit_assigned_run_time_vector(
        self, ast: field.AssignedRunTimeVector
    ) -> Dict[str, Any]:
        return {
            "assigned_run_time_vector": {
                "name": ast.name,
                "value": [str(v) for v in ast.value],
            }
        }

    def visit_field(self, ast: field.Field) -> Any:
        return {
            "field": {
                "value": [(self.visit(k), self.visit(v)) for k, v in ast.drives.items()]
            }
        }

    def visit_waveform(self, ast: waveform.Waveform) -> Any:
        return self.waveform_serializer.visit(ast)

    def visit_analog_circuit(self, ast: analog_circuit.AnalogCircuit) -> Any:
        return {
            "analog_circuit": {
                "sequence": self.visit(ast.sequence),
                "register": self.visit(ast.register),
                "static_params": ast.static_params,
                "batch_params": ast.batch_params,
                "order": ast.order,
            }
        }


class BloqadeIRSerializer(json.JSONEncoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.analog_circuit_serializer = AnalogCircuitSerializer()
        self.waveform_serializer = WaveformSerializer()
        self.scalar_serializer = ScalarSerilaizer()
        self.bloqade_seq_types = (
            analog_circuit.AnalogCircuit,
            location.AtomArrangement,
            location.ParallelRegister,
            analog_circuit.AnalogCircuit,
            sequence.SequenceExpr,
            pulse.PulseExpr,
            field.FieldExpr,
        )

    def default(self, o: Any) -> Any:
        if isinstance(o, self.bloqade_seq_types):
            return self.analog_circuit_serializer.visit(o)
        elif isinstance(o, waveform.Waveform):
            return self.waveform_serializer.visit(o)
        elif isinstance(o, scalar.Scalar):
            return self.scalar_serializer.visit(o)
        else:
            return super().default(o)


class BloqadeIRDeserializer:
    constructors = {
        "literal": scalar.Literal,
        "variable": scalar.Variable,
        "assigned_variable": scalar.AssignedVariable,
        "negative": scalar.Negative,
        "add": scalar.Add,
        "mul": scalar.Mul,
        "div": scalar.Div,
        "min": scalar.Min,
        "max": scalar.Max,
        "slice_scalar": scalar.Slice,
        "interval": scalar.Interval,
        "constant": waveform.Constant,
        "linear": waveform.Linear,
        "poly": waveform.Poly,
        "negative_waveform": waveform.Negative,
        "add_waveform": waveform.Add,
        "scale": waveform.Scale,
        "slice_waveform": waveform.Slice,
        "sample": waveform.Sample,
        "append_waveform": waveform.Append,
        "record": waveform.Record,
        "smooth": waveform.Smooth,
        "alligned": waveform.AlignedWaveform,
        "chain": location.Chain,
        "honeycomb": location.Honeycomb,
        "kagome": location.Kagome,
        "lieb": location.Lieb,
        "list_of_locations": location.ListOfLocations,
        "rectangular": location.Rectangular,
        "square": location.Square,
        "triangular": location.Triangular,
        "parallel_register": location.ParallelRegister,
        "sequence": sequence.Sequence,
        "named_sequence": sequence.NamedSequence,
        "append_sequence": sequence.Append,
        "slice_sequence": sequence.Slice,
        "pulse": pulse.Pulse,
        "append_pulse": pulse.Append,
        "named_pulse": pulse.NamedPulse,
        "slice_pulse": pulse.Slice,
        "location": field.Location,
        "scaled_locations": field.ScaledLocations,
        "uniform": field.Uniform,
        "run_time_vector": field.RunTimeVector,
        "assigned_run_time_vector": field.AssignedRunTimeVector,
        "field": field.Field,
        "analog_circuit": analog_circuit.AnalogCircuit,
    }

    @classmethod
    def object_hook(cls, obj):
        if isinstance(obj, dict) and len(obj) == 1:
            ((head, options),) = obj.items()
            if head in cls.constructors:
                return cls.constructors[head](**options)

        return obj
