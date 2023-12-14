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

from bloqade.ir.visitor import BloqadeIRVisitor, BloqadeNodeTypes

import json

from typing import Any, Dict


class BloqadeIRSerializer(json.JSONEncoder, BloqadeIRVisitor):
    def visit_scalar_Literal(self, node: scalar.Literal) -> Dict[str, Dict[str, str]]:
        return {"literal": {"value": str(node.value)}}

    def visit_scalar_AssignedVariable(
        self, node: scalar.AssignedVariable
    ) -> Dict[str, Any]:
        return {
            "assigned_variable": {
                "name": node.name,
                "value": str(node.value),
            }
        }

    def visit_scalar_Negative(self, node: scalar.Negative) -> Dict[str, Any]:
        return {"negative": {"expr": self.visit(node.expr)}}

    def visit_scalar_Add(self, node: scalar.Add) -> Dict[str, Any]:
        return {"add": {"lhs": self.visit(node.lhs), "rhs": self.visit(node.rhs)}}

    def visit_scalar_Mul(self, node: scalar.Mul) -> Dict[str, Any]:
        return {"mul": {"lhs": self.visit(node.lhs), "rhs": self.visit(node.rhs)}}

    def visit_scalar_Div(self, node: scalar.Div) -> Dict[str, Any]:
        return {"div": {"lhs": self.visit(node.lhs), "rhs": self.visit(node.rhs)}}

    def visit_scalar_Min(self, node: scalar.Min) -> Dict[str, Any]:
        return {"min": {"exprs": list(map(self.visit, node.exprs))}}

    def visit_scalar_Max(self, node: scalar.Max) -> Dict[str, Any]:
        return {"max": {"exprs": list(map(self.visit, node.exprs))}}

    def visit_scalar_Slice(self, node: scalar.Slice):
        return {
            "slice_scalar": {
                "expr": self.visit(node.expr),
                "interval": self.visit(node.interval),
            }
        }

    def visit_scalar_Interval(self, node: scalar.Interval) -> Dict[str, Any]:
        return {
            "interval": {
                "start": self.visit(node.start) if node.start is not None else None,
                "stop": self.visit(node.stop) if node.stop is not None else None,
            }
        }

    def visit_waveform_Constant(self, node: waveform.Constant) -> Dict[str, Any]:
        return {
            "constant": {
                "value": self.visit(node.value),
                "duration": self.visit(node.duration),
            }
        }

    def visit_waveform_Linear(self, node: waveform.Linear) -> Dict[str, Any]:
        return {
            "linear": {
                "start": self.visit(node.start),
                "stop": self.visit(node.stop),
                "duration": self.visit(node.duration),
            }
        }

    def visit_waveform_Poly(self, node: waveform.Poly) -> Dict[str, Any]:
        return {
            "poly": {
                "coeffs": list(map(self.visit, node.coeffs)),
                "duration": self.visit(node.duration),
            }
        }

    def visit_waveform_PythonFn(self, node: waveform.PythonFn) -> Dict[str, Any]:
        raise ValueError("Bloqade does not support serialization of Python code.")

    def visit_waveform_Negative(self, node: waveform.Negative) -> Dict[str, Any]:
        return {"negative_waveform": {"waveform": self.visit(node.waveform)}}

    def visit_waveform_Add(self, node: waveform.Add) -> Dict[str, Any]:
        return {
            "add_waveform": {
                "left": self.visit(node.left),
                "right": self.visit(node.right),
            }
        }

    def visit_waveform_Scale(self, node: waveform.Scale) -> Dict[str, Any]:
        return {
            "scale": {
                "waveform": self.visit(node.waveform),
                "scalar": self.visit(node.scalar),
            }
        }

    def visit_waveform_Slice(self, node: waveform.Slice) -> Dict[str, Any]:
        return {
            "slice_waveform": {
                "waveform": self.visit(node.waveform),
                "interval": self.visit(node.interval),
            }
        }

    def visit_waveform_Sample(self, node: waveform.Sample) -> Dict[str, Any]:
        return {
            "sample": {
                "waveform": self.visit(node.waveform),
                "dt": self.visit(node.dt),
                "interpolation": node.interpolation.value,
            }
        }

    def visit_waveform_Append(self, node: waveform.Append) -> Dict[str, Any]:
        return {"append_waveform": {"waveforms": list(map(self.visit, node.waveforms))}}

    def visit_waveform_Record(self, node: waveform.Record) -> Dict[str, Any]:
        return {
            "record": {
                "var": self.visit(node.var),
                "waveform": self.visit(node.waveform),
            }
        }

    def visit_waveform_Smooth(self, node: waveform.Smooth) -> Dict[str, Any]:
        return {
            "smooth": {
                "waveform": self.visit(node.waveform),
                "radius": self.visit(node.radius),
                "kernel": type(node.kernel).__name__,
            }
        }

    def visit_waveform_AllignedWaveform(
        self, node: waveform.AlignedWaveform
    ) -> Dict[str, Any]:
        if isinstance(node.value, scalar.Scalar):
            value = self.visit(node.value)
        else:
            value = node.value.value
        return {
            "alligned": {
                "waveform": self.visit(node.waveform),
                "allignment": self.visit(node.allignment),
                "value": value,
            }
        }

    def visit_bravais_Chain(self, node: Chain) -> Any:
        return {
            "chain": {
                "lattice_spacing": self.visit(node.lattice_spacing),
                "L": node.L,
                "vertical_chain": node.vertical_chain,
            }
        }

    def visit_bravais_Honeycomb(self, node: Honeycomb) -> Any:
        return {
            "honeycomb": {
                "lattice_spacing": self.visit(node.lattice_spacing),
                "L1": node.shape[0],
                "L2": node.shape[1],
            }
        }

    def visit_bravais_Kagome(self, node: Kagome) -> Any:
        return {
            "kagome": {
                "lattice_spacing": self.visit(node.lattice_spacing),
                "L1": node.shape[0],
                "L2": node.shape[1],
            }
        }

    def visit_bravais_Lieb(self, node: Lieb) -> Any:
        return {
            "lieb": {
                "lattice_spacing": self.visit(node.lattice_spacing),
                "L1": node.shape[0],
                "L2": node.shape[1],
            }
        }

    def visit_locaiton_LocationInfo(self, node: LocationInfo) -> Any:
        return {
            "location_info": {
                "position": [[self.visit(x), self.visit(y)] for x, y in node.position],
                "filling": node.filling.value,
            }
        }

    def visit_location_ListOfLocations(self, node: ListOfLocations) -> Any:
        return {
            "list_of_locations": {
                "location_list": list(map(self.visit, node.location_list))
            }
        }

    def visit_bravais_Rectangular(self, node: Rectangular) -> Any:
        return {
            "rectangular": {
                "lattice_spacing_x": self.visit(node.lattice_spacing_x),
                "lattice_spacing_y": self.visit(node.lattice_spacing_y),
                "width": node.width,
                "height": node.height,
            }
        }

    def visit_bravais_Square(self, node: Square) -> Any:
        return {
            "square": {
                "lattice_spacing": self.visit(node.lattice_spacing),
                "L1": node.shape[0],
                "L2": node.shape[1],
            }
        }

    def visit_bravais_Triangular(self, node: Triangular) -> Any:
        return {
            "triangular": {
                "lattice_spacing": self.visit(node.lattice_spacing),
                "L1": node.shape[0],
                "L2": node.shape[1],
            }
        }

    def visit_location_ParallelRegister(self, node: ParallelRegister) -> Any:
        return {
            "parallel_register": {
                "register": self.visit(node.register),
                "cluster_spacing": self.visit(node.cluster_spacing),
            }
        }

    def visit_sequence_Sequence(self, node: sequence.Sequence) -> Dict[str, Any]:
        object_to_str = {
            sequence.rydberg: "rydberg",
            sequence.hyperfine: "hyperfine",
        }
        return {
            "sequence": {
                "pulses": {
                    object_to_str[k]: self.visit(v) for k, v in node.pulses.items()
                }
            }
        }

    def visit_sequence_NamedSequence(
        self, node: sequence.NamedSequence
    ) -> Dict[str, Any]:
        return {
            "named_sequence": {
                "name": node.name,
                "sub_sequence": self.visit(node.sub_sequence),
            }
        }

    def visit_sequence_Append(self, node: sequence.Append) -> Dict[str, Any]:
        return {
            "append_sequence": {"sequences": [self.visit(s) for s in node.sequences]}
        }

    def visit_sequence_Slice(self, node: sequence.Slice) -> Dict[str, Any]:
        return {
            "slice_sequence": {
                "sequence": self.visit(node.sequence),
                "interval": self.visit(node.interval),
            }
        }

    def visit_pulse_Pulse(self, node: pulse.Pulse):
        object_map_str = {
            pulse.detuning: "detuning",
            pulse.rabi.amplitude: "rabi_frequency_amplitude",
            pulse.rabi.phase: "rabi_frequency_phase",
        }
        return {
            "pulse": {
                "fields": {
                    object_map_str[k]: self.visit(v) for k, v in node.fields.items()
                }
            }
        }

    def visit_pulse_Append(self, node: pulse.Append) -> Dict[str, Any]:
        return {"append_pulse": {"pulses": [self.visit(p) for p in node.pulses]}}

    def visit_pulse_NamedPulse(self, node: pulse.NamedPulse) -> Dict[str, Any]:
        return {
            "named_pulse": {"name": node.name, "sub_pulse": self.visit(node.sub_pulse)}
        }

    def visit_pulse_Slice(self, node: pulse.Slice) -> Dict[str, Any]:
        return {
            "slice_pulse": {
                "pulse": self.visit(node.sub_pulse),
                "interval": self.visit(node.interval),
            }
        }

    def visit_field_Location(self, node: field.Location) -> Dict[str, Any]:
        return {"location": {"label": node.label}}

    def visit_field_ScaledLocations(
        self, node: field.ScaledLocations
    ) -> Dict[str, Any]:
        return {
            "scaled_locations": [
                (self.visit(k), self.visit(v)) for k, v in node.items()
            ]
        }

    def visit_field_Uniform(self, node: field.Uniform) -> Dict[str, Any]:
        return {"uniform": {}}

    def visit_field_RunTimeVector(self, node: field.RunTimeVector) -> Dict[str, Any]:
        return {"run_time_vector": {"name": node.name}}

    def visit_field_AssignedRunTimeVector(
        self, node: field.AssignedRunTimeVector
    ) -> Dict[str, Any]:
        return {
            "assigned_run_time_vector": {
                "name": node.name,
                "value": [str(v) for v in node.value],
            }
        }

    def visit_field_Field(self, node: field.Field) -> Any:
        return {
            "field": {
                "value": [
                    (self.visit(k), self.visit(v)) for k, v in node.drives.items()
                ]
            }
        }

    def visit_analog_circuit_AnalogCircuit(
        self, node: analog_circuit.AnalogCircuit
    ) -> Any:
        return {
            "analog_circuit": {
                "sequence": self.visit(node.sequence),
                "register": self.visit(node.register),
                "static_params": node.static_params,
                "batch_params": node.batch_params,
                "order": node.order,
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
