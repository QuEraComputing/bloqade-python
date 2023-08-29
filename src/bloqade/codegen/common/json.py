import bloqade.ir.location as location
import bloqade.ir.control.sequence as sequence
import bloqade.ir.control.pulse as pulse
import bloqade.ir.control.field as field
import bloqade.ir.analog_circuit as analog_circuit
import bloqade.ir.control.waveform as waveform
import bloqade.ir.scalar as scalar

from bloqade.ir.visitor.analog_circuit import AnalogCircuitVisitor
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
            "default_variable": {
                "name": ast.name,
                "default_value": str(ast.value),
            }
        }

    def visit_negative(self, ast: scalar.Negative) -> Dict[str, Any]:
        return {"negative": {"expr": self.visit(ast.expr)}}

    def visit_add(self, ast: scalar.Add) -> Dict[str, Any]:
        return {"add": {"lhs": self.visit(ast.left), "rhs": self.visit(ast.right)}}

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
        match (ast.start, ast.stop):
            case (None, _):
                return {"interval": {"stop": self.visit(ast.stop)}}
            case (_, None):
                return {"interval": {"start": self.visit(ast.start)}}
            case (_, _):
                return {
                    "interval": {
                        "start": self.visit(ast.start),
                        "stop": self.visit(ast.stop),
                    }
                }
            case _:
                raise ValueError(f"Invalid Interval({ast.start}, {ast.stop})")

    def default(self, obj: Any) -> Dict[str, Any]:
        print(obj, type(obj))
        if isinstance(obj, scalar.Scalar):
            return self.visit(obj)

        return super().default(obj)


class WaveformSerializer(WaveformVisitor):
    def __init__(self):
        self.scalar_encoder = ScalarSerilaizer()

    def visit_constant(self, ast: waveform.Constant) -> Dict[str, Any]:
        return {"constant": {"value": self.scalar_encoder.visit(ast.value)}}

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
        return {"negative": {"waveform": self.visit(ast.waveform)}}

    def visit_add(self, ast: waveform.Add) -> Dict[str, Any]:
        return {"add": {"left": self.visit(ast.left), "right": self.visit(ast.right)}}

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
        match ast.kernel:
            case waveform.Gaussian:
                kernel = "gaussian"
            case waveform.Logistic:
                kernel = "logistic"
            case waveform.Sigmoid:
                kernel = "sigmoid"
            case waveform.Triangle:
                kernel = "triangle"
            case waveform.Uniform:
                kernel = "uniform"
            case waveform.Parabolic:
                kernel = "parabolic"
            case waveform.Biweight:
                kernel = "biweight"
            case waveform.Triweight:
                kernel = "triweight"
            case waveform.Tricube:
                kernel = "tricube"
            case waveform.Cosine:
                kernel = "cosine"

        return {
            "smooth": {
                "waveform": self.visit(ast.waveform),
                "radius": self.scalar_encoder.visit(ast.radius),
                "kernel": kernel,
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


class ProgramSerializer(AnalogCircuitVisitor):
    def __init__(self) -> None:
        self.waveform_serializer = WaveformSerializer()
        self.scalar_serializer = ScalarSerilaizer()

    def visit_register(self, ast: location.AtomArrangement) -> Any:
        match ast:
            case location.ListOfLocations(locations):
                locations = [
                    {
                        "location_info": {
                            "position": list(
                                map(self.scalar_serializer.visit, info.position)
                            ),
                            "filling": info.filling.value,
                        }
                    }
                    for info in locations
                ]
                return {"list_of_locations": locations}
            case location.Chain(shape, lattice_spacing):
                return {
                    "chain": {
                        "lattice_spacing": self.visit(lattice_spacing),
                        "L": shape[0],
                    }
                }
            case location.Square(shape, lattice_spacing):
                return {
                    "square": {
                        "lattice_spacing": self.visit(lattice_spacing),
                        "L": shape[0],
                    }
                }
            case location.Honeycomb(shape, lattice_spacing):
                return {
                    "honeycomb": {
                        "lattice_spacing": self.visit(lattice_spacing),
                        "L": shape[0],
                    }
                }
            case location.Triangular(shape, lattice_spacing):
                return {
                    "triangular": {
                        "lattice_spacing": self.visit(lattice_spacing),
                        "L": shape[0],
                    }
                }
            case location.Lieb(shape, lattice_spacing):
                return {
                    "lieb": {
                        "lattice_spacing": self.visit(lattice_spacing),
                        "L": shape[0],
                    }
                }
            case location.Kagome(shape, lattice_spacing):
                return {
                    "kagome": {
                        "lattice_spacing": self.visit(lattice_spacing),
                        "L": shape[0],
                    }
                }
            case location.Rectangular(shape, lattice_spacing_x, lattice_spacing_y):
                return {
                    "rectangular": {
                        "lattice_spacing_x": self.visit(lattice_spacing_x),
                        "lattice_spacing_y": self.visit(lattice_spacing_y),
                        "width": shape[0],
                        "height": shape[1],
                    }
                }

    def visit_parallel_register(self, ast: location.ParallelRegister) -> Any:
        return {
            "parallel_register": {
                "register": self.visit(ast._register),
                "cluster_spacing": self.visit(ast._cluster_spacing),
            }
        }

    def visit_sequence(self, ast: sequence.SequenceExpr) -> Any:
        match ast:
            case sequence.Sequence(pulses):
                object_map_str = {
                    sequence.rydberg: "rydberg",
                    sequence.hyperfine: "hyperfine",
                }
                return {
                    "sequence": {
                        "pulses": {
                            object_map_str[k]: self.visit(v) for k, v in pulses.items()
                        }
                    }
                }
            case sequence.Append(sequences):
                return {
                    "append_sequence": {"sequences": [self.visit(s) for s in sequences]}
                }
            case sequence.NamedSequence(sub_sequence, name):
                return {
                    "named_sequence": {
                        "name": name,
                        "sub_sequence": self.visit(sub_sequence),
                    }
                }
            case sequence.Slice(sub_sequence, interval):
                return {
                    "slice_sequence": {
                        "sequence": self.visit(sub_sequence),
                        "interval": self.scalar_serializer.visit(interval),
                    }
                }

    def visit_pulse(self, ast: pulse.PulseExpr) -> Any:
        match ast:
            case pulse.Pulse(fields):
                object_map_str = {
                    pulse.detuning: "detuning",
                    pulse.rabi.amplitude: "rabi_frequency_amplitude",
                    pulse.rabi.phase: "rabi_frequency_phase",
                }
                return {
                    "pulse": {
                        "fields": {
                            object_map_str[k]: self.visit(v) for k, v in fields.items()
                        }
                    }
                }
            case pulse.Append(pulses):
                return {"append_pulse": {"pulses": [self.visit(p) for p in pulses]}}
            case pulse.NamedPulse(name, sub_pulse):
                return {
                    "named_pulse": {"name": name, "sub_pulse": self.visit(sub_pulse)}
                }
            case pulse.Slice(sub_pulse, interval):
                return {
                    "slice_pulse": {
                        "pulse": self.visit(sub_pulse),
                        "interval": self.scalar_serializer.visit(interval),
                    }
                }

    def visit_spatial_modulation(self, ast: field.SpatialModulation) -> Any:
        match ast:
            case field.ScaledLocations(value):
                return {
                    "scaled_locations": [
                        (self.visit(k), self.visit(v)) for k, v in value.items()
                    ]
                }
            case field.Uniform:
                return "uniform"
            case field.RunTimeVector(name):
                return {"run_time_vector": {"name": name}}

    def visit_field(self, ast: field.Field) -> Any:
        return {
            "field": {
                "value": [(self.visit(k), self.visit(v)) for k, v in ast.value.items()]
            }
        }

    def visit_waveform(self, ast: waveform.Waveform) -> Any:
        return self.waveform_serializer.visit(ast)

    def visit_analog_circuit(self, ast: analog_circuit.AnalogCircuit) -> Any:
        return {
            "bloqade_program": {
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
        self.program_serializer = ProgramSerializer()
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
            return self.program_serializer.visit(o)
        elif isinstance(o, waveform.Waveform):
            return self.waveform_serializer.visit(o)
        elif isinstance(o, scalar.Scalar):
            return self.scalar_serializer.visit(o)
        else:
            return super().default(o)


class BloqadeIRDeserializer:
    def is_register_obj(self, obj: Dict[str, Any]) -> bool:
        return (
            "list_of_locations" in obj
            or "chain" in obj
            or "square" in obj
            or "honeycomb" in obj
            or "triangular" in obj
            or "lieb" in obj
            or "kagome" in obj
            or "rectangular" in obj
            or "parallel_register" in obj
        )

    def is_sequence_obj(self, obj: Dict[str, Any]) -> bool:
        return (
            "sequence" in obj
            or "append_sequence" in obj
            or "named_sequence" in obj
            or "slice_sequence" in obj
        )

    def is_pulse_obj(self, obj: Dict[str, Any]) -> bool:
        return (
            "pulse" in obj
            or "append_pulse" in obj
            or "named_pulse" in obj
            or "slice_pulse" in obj
        )

    def is_field_obj(self, obj: Dict[str, Any]) -> bool:
        return (
            "field" in obj
            or "scaled_locations" in obj
            or "uniform" in obj
            or "run_time_vector" in obj
        )

    def is_waveform_obj(self, obj: Dict[str, Any]) -> bool:
        return (
            "constant" in obj
            or "linear" in obj
            or "poly" in obj
            or "negative" in obj
            or "add" in obj
            or "scale" in obj
            or "slice_waveform" in obj
            or "sample" in obj
            or "append_waveform" in obj
            or "record" in obj
            or "smooth" in obj
            or "alligned" in obj
        )

    def is_scalar_obj(self, obj: Dict[str, Any]) -> bool:
        return (
            "literal" in obj
            or "variable" in obj
            or "default_variable" in obj
            or "negative" in obj
            or "add" in obj
            or "mul" in obj
            or "div" in obj
            or "min" in obj
            or "max" in obj
            or "slice_scalar" in obj
            or "interval" in obj
        )

    def is_bloqade_ir(self, obj: Dict[str, Any]) -> bool:
        return (
            self.is_scalar_obj(obj)
            or self.is_waveform_obj(obj)
            or self.is_field_obj(obj)
            or self.is_pulse_obj(obj)
            or self.is_sequence_obj(obj)
            or self.is_register_obj(obj)
            or "bloqade_program" in obj
        )

    def scalar_hook(self, obj: Dict[str, Any]):
        from decimal import Decimal

        match obj:
            case {"literal": {"value": str(value)}}:
                return scalar.Literal(Decimal(value))
            case {"variable": {"name": str(name)}}:
                return scalar.Variable(name)
            case {"default_variable": {"name": str(name), "default_value": str(value)}}:
                return scalar.AssignedVariable(name, Decimal(value))
            case {"negative": {"expr": expr}}:
                return scalar.Negative(expr)
            case {"add": {"lhs": lhs, "rhs": rhs}}:
                return scalar.Add(lhs, rhs)
            case {"mul": {"lhs": lhs, "rhs": rhs}}:
                return scalar.Mul(lhs, rhs)
            case {"div": {"lhs": lhs, "rhs": rhs}}:
                return scalar.Div(lhs, rhs)
            case {"min": {"exprs": exprs}}:
                return scalar.Min(frozenset(exprs))
            case {"max": {"exprs": exprs}}:
                return scalar.Max(frozenset(exprs))
            case {"slice_scalar": {"expr": expr, "interval": interval}}:
                return scalar.Slice(expr, interval)
            case {"interval": {"start": start, "stop": stop}}:
                return scalar.Interval(start, stop)
            case {"interval": {"start": start}}:
                return scalar.Interval(start, None)
            case {"interval": {"stop": stop}}:
                return scalar.Interval(None, stop)
            case _:
                return obj

    def waveform_hook(self, obj: Dict[str, Any]):
        match obj:
            case {"constant": {"value": value}}:
                return waveform.Constant(BloqadeIRDeserializer.object_hook(value))
            case {"linear": {"start": start, "stop": stop, "duration": duration}}:
                return waveform.Linear(start, stop, duration)
            case {"poly": {"coeffs": coeffs, "duration": duration}}:
                return waveform.Poly(coeffs, duration)
            case {"negative": {"waveform": sub_waveform}}:
                return waveform.Negative(sub_waveform)
            case {"add": {"left": left, "right": right}}:
                return waveform.Add(left, right)
            case {"scale": {"waveform": sub_waveform, "scalar": scale}}:
                return waveform.Scale(sub_waveform, scale)
            case {"slice_waveform": {"waveform": sub_waveform, "interval": interval}}:
                return waveform.Slice(sub_waveform, interval)
            case {
                "sample": {
                    "waveform": sub_waveform,
                    "dt": dt,
                    "interpolation": interpolation,
                }
            }:
                return waveform.Sample(sub_waveform, dt, interpolation)
            case {"append_waveform": {"waveforms": waveforms}}:
                return waveform.Append(waveforms)
            case {"record": {"var": var, "waveform": sub_waveform}}:
                return waveform.Record(var, sub_waveform)
            case {
                "smooth": {
                    "waveform": sub_waveform,
                    "radius": radius,
                    "kernel": kernel_str,
                }
            }:
                match kernel_str:
                    case "gaussian":
                        kernel = waveform.Gaussian
                    case "logistic":
                        kernel = waveform.Logistic
                    case "sigmoid":
                        kernel = waveform.Sigmoid
                    case "triangle":
                        kernel = waveform.Triangle
                    case "uniform":
                        kernel = waveform.Uniform
                    case "parabolic":
                        kernel = waveform.Parabolic
                    case "biweight":
                        kernel = waveform.Biweight
                    case "triweight":
                        kernel = waveform.Triweight
                    case "tricube":
                        kernel = waveform.Tricube
                    case "cosine":
                        kernel = waveform.Cosine
                    case _:
                        raise ValueError(f"Invalid kernel: {kernel_str}")

                return waveform.Smooth(radius, kernel, sub_waveform)
            case {
                "alligned": {
                    "waveform": sub_waveform,
                    "allignment": allignment,
                    "value": value_obj,
                }
            }:
                match value_obj:
                    case str():
                        value = waveform.AlignedValue(value_obj)
                    case _:
                        value = value_obj

                return waveform.AlignedWaveform(sub_waveform, allignment, value)
            case _:
                raise ValueError(f"Invalid waveform json: {obj}")

    def register_hook(self, obj: Dict[str, Any]):
        match obj:
            case {"location_info": {"position": position, "filling": filling_str}}:
                return location.LocationInfo(
                    tuple(position), location.Filling(filling_str)
                )
            case {"list_of_locations": locations}:
                return location.ListOfLocations(locations)
            case {"chain": {"lattice_spacing": lattice_spacing, "L": L}}:
                return location.Chain(L, lattice_spacing)
            case {"square": {"lattice_spacing": lattice_spacing, "L": L}}:
                return location.Square(L, lattice_spacing)
            case {"honeycomb": {"lattice_spacing": lattice_spacing, "L": L}}:
                return location.Honeycomb(L, lattice_spacing)
            case {"triangular": {"lattice_spacing": lattice_spacing, "L": L}}:
                return location.Triangular(L, lattice_spacing)
            case {"lieb": {"lattice_spacing": lattice_spacing, "L": L}}:
                return location.Lieb(L, lattice_spacing)
            case {"kagome": {"lattice_spacing": lattice_spacing, "L": L}}:
                return location.Kagome(L, lattice_spacing)
            case {
                "rectangular": {
                    "lattice_spacing_x": lattice_spacing_x,
                    "lattice_spacing_y": lattice_spacing_y,
                    "width": width,
                    "height": height,
                }
            }:
                return location.Rectangular(
                    width,
                    height,
                    lattice_spacing_x,
                    lattice_spacing_y,
                )
            case {
                "parallel_register": {
                    "register": register,
                    "cluster_spacing": cluster_spacing,
                }
            }:
                return location.ParallelRegister(register, cluster_spacing)
            case _:
                raise ValueError(f"Invalid register json: {obj}")

    def field_hook(self, obj: Dict[str, Any]):
        match obj:
            case {"location": {"value": int(loc)}}:
                return field.Location(loc)
            case {"scaled_locations": {"pairs": pairs}}:
                return field.ScaledLocations(dict(pairs))
            case "uniform":
                return field.Uniform
            case {"run_time_vector": {"name": name}}:
                return field.RunTimeVector(name)
            case {"field": {"value": value}}:
                return field.Field(dict(value))
            case _:
                raise ValueError(f"Invalid field json: {obj}")

    def pulse_hook(self, obj: Dict[str, Any]):
        match obj:
            case {"pulse": {"fields": fields}}:
                str_map_object = {
                    "detuning": pulse.detuning,
                    "rabi_frequency_amplitude": pulse.rabi.amplitude,
                    "rabi_frequency_phase": pulse.rabi.phase,
                }
                return pulse.Pulse(
                    dict(map(lambda k, v: (str_map_object[k], k), fields))
                )
            case {"append_pulse": {"pulses": pulses}}:
                return pulse.Append(pulses)
            case {"named_pulse": {"name": name, "sub_pulse": sub_pulse}}:
                return pulse.NamedPulse(name, sub_pulse)
            case {"slice_pulse": {"pulse": sub_pulse, "interval": interval}}:
                return pulse.Slice(sub_pulse, interval)
            case _:
                raise ValueError(f"Invalid pulse json: {obj}")

    def sequence_hook(self, obj: Dict[str, Any]):
        match obj:
            case {"sequence": {"pulses": pulses}}:
                str_map_object = {
                    "rydberg": sequence.rydberg,
                    "hyperfine": sequence.hyperfine,
                }
                return sequence.Sequence(
                    dict(map(lambda k, v: (str_map_object[k], k), pulses))
                )
            case {"append_sequence": {"sequences": sequences}}:
                return sequence.Append(
                    list(map(BloqadeIRDeserializer.object_hook, sequences))
                )
            case {"named_sequence": {"name": name, "sub_sequence": sub_sequence}}:
                return sequence.NamedSequence(sub_sequence, name)
            case {"slice_sequence": {"sequence": sub_sequence, "interval": interval}}:
                return sequence.Slice(sub_sequence, interval)
            case _:
                raise ValueError(f"Invalid sequence json: {obj}")

    def object_hook(self, obj: Dict[str, Any]):
        if self.is_scalar_obj(obj):
            return self.scalar_hook(obj)
        elif self.is_waveform_obj(obj):
            return self.waveform_hook(obj)
        elif self.is_field_obj(obj):
            return self.field_hook(obj)
        elif self.is_pulse_obj(obj):
            return self.pulse_hook(obj)
        elif self.is_sequence_obj(obj):
            return self.sequence_hook(obj)
        elif self.is_register_obj(obj):
            return self.register_hook(obj)
        elif "bloqade_program" in obj:
            return analog_circuit.AnalogCircuit(
                register=self.register_hook(obj["bloqade_program"]["register"]),
                sequence=self.sequence_hook(obj["bloqade_program"]["sequence"]),
                static_params=obj["bloqade_program"]["static_params"],
                batch_params=obj["bloqade_program"]["batch_params"],
                order=tuple(obj["bloqade_program"]["order"]),
            )
        else:
            return obj
