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
from bloqade.ir.location.location import LocationInfo, ParallelRegister
import bloqade.ir.scalar as scalar

from bloqade.ir.visitor.base import BloqadeIRVisitor, BloqadeNodeTypes

import json

from typing import Any, Dict


class BloqadeIRSerializer(json.JSONEncoder, BloqadeIRVisitor):
    def visit_scalar_Literal(self, ast: scalar.Literal) -> Dict[str, Dict[str, str]]:
        return {"literal": {"value": str(ast.value)}}

    def visit_scalar_AssignedVariable(
        self, ast: scalar.AssignedVariable
    ) -> Dict[str, Any]:
        return {
            "assigned_variable": {
                "name": ast.name,
                "value": str(ast.value),
            }
        }

    def visit_scalar_Negative(self, ast: scalar.Negative) -> Dict[str, Any]:
        return {"negative": {"expr": self.visit(ast.expr)}}

    def visit_scalar_Add(self, ast: scalar.Add) -> Dict[str, Any]:
        return {"add": {"lhs": self.visit(ast.lhs), "rhs": self.visit(ast.rhs)}}

    def visit_scalar_Mul(self, ast: scalar.Mul) -> Dict[str, Any]:
        return {"mul": {"lhs": self.visit(ast.lhs), "rhs": self.visit(ast.rhs)}}

    def visit_scalar_Div(self, ast: scalar.Div) -> Dict[str, Any]:
        return {"div": {"lhs": self.visit(ast.lhs), "rhs": self.visit(ast.rhs)}}

    def visit_scalar_Min(self, ast: scalar.Min) -> Dict[str, Any]:
        return {"min": {"exprs": list(map(self.visit, ast.exprs))}}

    def visit_scalar_Max(self, ast: scalar.Max) -> Dict[str, Any]:
        return {"max": {"exprs": list(map(self.visit, ast.exprs))}}

    def visit_scalar_Slice(self, ast: scalar.Slice):
        return {
            "slice_scalar": {
                "expr": self.visit(ast.expr),
                "interval": self.visit(ast.interval),
            }
        }

    def visit_scalar_Interval(self, ast: scalar.Interval) -> Dict[str, Any]:
        return {
            "interval": {
                "start": self.visit(ast.start) if ast.start is not None else None,
                "stop": self.visit(ast.stop) if ast.stop is not None else None,
            }
        }

    def visit_waveform_Constant(self, ast: waveform.Constant) -> Dict[str, Any]:
        return {
            "constant": {
                "value": self.visit(ast.value),
                "duration": self.visit(ast.duration),
            }
        }

    def visit_waveform_Linear(self, ast: waveform.Linear) -> Dict[str, Any]:
        return {
            "linear": {
                "start": self.visit(ast.start),
                "stop": self.visit(ast.stop),
                "duration": self.visit(ast.duration),
            }
        }

    def visit_waveform_Poly(self, ast: waveform.Poly) -> Dict[str, Any]:
        return {
            "poly": {
                "coeffs": list(map(self.visit, ast.coeffs)),
                "duration": self.visit(ast.duration),
            }
        }

    def visit_waveform_PythonFn(self, ast: waveform.PythonFn) -> Dict[str, Any]:
        raise ValueError("Bloqade does not support serialization of Python code.")

    def visit_waveform_Negative(self, ast: waveform.Negative) -> Dict[str, Any]:
        return {"negative_waveform": {"waveform": self.visit(ast.waveform)}}

    def visit_waveform_Add(self, ast: waveform.Add) -> Dict[str, Any]:
        return {
            "add_waveform": {
                "left": self.visit(ast.left),
                "right": self.visit(ast.right),
            }
        }

    def visit_waveform_Scale(self, ast: waveform.Scale) -> Dict[str, Any]:
        return {
            "scale": {
                "waveform": self.visit(ast.waveform),
                "scalar": self.visit(ast.scalar),
            }
        }

    def visit_waveform_Slice(self, ast: waveform.Slice) -> Dict[str, Any]:
        return {
            "slice_waveform": {
                "waveform": self.visit(ast.waveform),
                "interval": self.visit(ast.interval),
            }
        }

    def visit_waveform_Sample(self, ast: waveform.Sample) -> Dict[str, Any]:
        return {
            "sample": {
                "waveform": self.visit(ast.waveform),
                "dt": self.visit(ast.dt),
                "interpolation": ast.interpolation.value,
            }
        }

    def visit_waveform_Append(self, ast: waveform.Append) -> Dict[str, Any]:
        return {"append_waveform": {"waveforms": list(map(self.visit, ast.waveforms))}}

    def visit_waveform_Record(self, ast: waveform.Record) -> Dict[str, Any]:
        return {
            "record": {
                "var": self.visit(ast.var),
                "waveform": self.visit(ast.waveform),
            }
        }

    def visit_waveform_Smooth(self, ast: waveform.Smooth) -> Dict[str, Any]:
        return {
            "smooth": {
                "waveform": self.visit(ast.waveform),
                "radius": self.visit(ast.radius),
                "kernel": type(ast.kernel).__name__,
            }
        }

    def visit_waveform_AllignedWaveform(
        self, ast: waveform.AlignedWaveform
    ) -> Dict[str, Any]:
        if isinstance(ast.value, scalar.Scalar):
            value = self.visit(ast.value)
        else:
            value = ast.value.value
        return {
            "alligned": {
                "waveform": self.visit(ast.waveform),
                "allignment": self.visit(ast.allignment),
                "value": value,
            }
        }

    def visit_bravais_Chain(self, ast: Chain) -> Any:
        return {
            "chain": {
                "lattice_spacing": self.visit(ast.lattice_spacing),
                "L": ast.L,
                "vertical_chain": ast.vertical_chain,
            }
        }

    def visit_bravais_Honeycomb(self, ast: Honeycomb) -> Any:
        return {
            "honeycomb": {
                "lattice_spacing": self.visit(ast.lattice_spacing),
                "L1": ast.shape[0],
                "L2": ast.shape[1],
            }
        }

    def visit_bravais_Kagome(self, ast: Kagome) -> Any:
        return {
            "kagome": {
                "lattice_spacing": self.visit(ast.lattice_spacing),
                "L1": ast.shape[0],
                "L2": ast.shape[1],
            }
        }

    def visit_bravais_Lieb(self, ast: Lieb) -> Any:
        return {
            "lieb": {
                "lattice_spacing": self.visit(ast.lattice_spacing),
                "L1": ast.shape[0],
                "L2": ast.shape[1],
            }
        }

    def visit_locaiton_LocationInfo(self, ast: LocationInfo) -> Any:
        return {
            "location_info": {
                "position": [[self.visit(x), self.visit(y)] for x, y in ast.position],
                "filling": ast.filling.value,
            }
        }

    def visit_location_ListOfLocations(self, ast: ListOfLocations) -> Any:
        return {
            "list_of_locations": {
                "location_list": list(map(self.visit, ast.location_list))
            }
        }

    def visit_bravais_Rectangular(self, ast: Rectangular) -> Any:
        return {
            "rectangular": {
                "lattice_spacing_x": self.visit(ast.lattice_spacing_x),
                "lattice_spacing_y": self.visit(ast.lattice_spacing_y),
                "width": ast.width,
                "height": ast.height,
            }
        }

    def visit_bravais_Square(self, ast: Square) -> Any:
        return {
            "square": {
                "lattice_spacing": self.visit(ast.lattice_spacing),
                "L1": ast.shape[0],
                "L2": ast.shape[1],
            }
        }

    def visit_bravais_Triangular(self, ast: Triangular) -> Any:
        return {
            "triangular": {
                "lattice_spacing": self.visit(ast.lattice_spacing),
                "L1": ast.shape[0],
                "L2": ast.shape[1],
            }
        }

    def visit_location_ParallelRegister(self, ast: ParallelRegister) -> Any:
        return {
            "parallel_register": {
                "register": self.visit(ast.register),
                "cluster_spacing": self.visit(ast.cluster_spacing),
            }
        }

    def visit_sequence_Sequence(self, ast: sequence.Sequence) -> Dict[str, Any]:
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

    def visit_sequence_NamedSequence(
        self, ast: sequence.NamedSequence
    ) -> Dict[str, Any]:
        return {
            "named_sequence": {
                "name": ast.name,
                "sub_sequence": self.visit(ast.sub_sequence),
            }
        }

    def visit_sequence_Append(self, ast: sequence.Append) -> Dict[str, Any]:
        return {
            "append_sequence": {"sequences": [self.visit(s) for s in ast.sequences]}
        }

    def visit_sequence_Slice(self, ast: sequence.Slice) -> Dict[str, Any]:
        return {
            "slice_sequence": {
                "sequence": self.visit(ast.sequence),
                "interval": self.visit(ast.interval),
            }
        }

    def visit_pulse_Pulse(self, ast: pulse.Pulse):
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

    def visit_pulse_Append(self, ast: pulse.Append) -> Dict[str, Any]:
        return {"append_pulse": {"pulses": [self.visit(p) for p in ast.pulses]}}

    def visit_pulse_NamedPulse(self, ast: pulse.NamedPulse) -> Dict[str, Any]:
        return {
            "named_pulse": {"name": ast.name, "sub_pulse": self.visit(ast.sub_pulse)}
        }

    def visit_pulse_Slice(self, ast: pulse.Slice) -> Dict[str, Any]:
        return {
            "slice_pulse": {
                "pulse": self.visit(ast.sub_pulse),
                "interval": self.visit(ast.interval),
            }
        }

    def visit_field_Location(self, ast: field.Location) -> Dict[str, Any]:
        return {"location": {"label": ast.label}}

    def visit_field_ScaledLocations(self, ast: field.ScaledLocations) -> Dict[str, Any]:
        return {
            "scaled_locations": [(self.visit(k), self.visit(v)) for k, v in ast.items()]
        }

    def visit_field_Uniform(self, ast: field.Uniform) -> Dict[str, Any]:
        return {"uniform": {}}

    def visit_field_RunTimeVector(self, ast: field.RunTimeVector) -> Dict[str, Any]:
        return {"run_time_vector": {"name": ast.name}}

    def visit_field_AssignedRunTimeVector(
        self, ast: field.AssignedRunTimeVector
    ) -> Dict[str, Any]:
        return {
            "assigned_run_time_vector": {
                "name": ast.name,
                "value": [str(v) for v in ast.value],
            }
        }

    def visit_field_Field(self, ast: field.Field) -> Any:
        return {
            "field": {
                "value": [(self.visit(k), self.visit(v)) for k, v in ast.drives.items()]
            }
        }

    def visit_analog_circuit_AnalogCircuit(
        self, ast: analog_circuit.AnalogCircuit
    ) -> Any:
        return {
            "analog_circuit": {
                "sequence": self.visit(ast.sequence),
                "register": self.visit(ast.register),
                "static_params": ast.static_params,
                "batch_params": ast.batch_params,
                "order": ast.order,
            }
        }

    def default(self, obj: Any) -> Any:
        if isinstance(obj, BloqadeNodeTypes):
            return self.visit(obj)
        else:
            return super().default(obj)


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
