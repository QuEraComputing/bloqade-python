import bloqade.ir.location as location
import bloqade.ir.control.sequence as sequence
import bloqade.ir.control.pulse as pulse
import bloqade.ir.control.field as field
import bloqade.ir.program as program
import bloqade.ir.control.waveform as waveform
import bloqade.ir.scalar as scalar


from bloqade.ir.visitor.program import ProgramVisitor
from bloqade.ir.visitor.waveform import WaveformVisitor
from bloqade.ir.visitor.scalar import ScalarVisitor

import json

from typing import Any, Dict


class ScalarSerilaizer(ScalarVisitor):
    def visit_literal(self, ast: scalar.Literal) -> Dict[str, Dict[str, str]]:
        return {"literal": {"value": str(ast.value)}}

    def visit_variable(self, ast: scalar.Variable) -> Dict[str, Dict[str, str]]:
        return {"variable": {"name": ast.name}}

    def visit_default_variable(self, ast: scalar.DefaultVariable) -> Dict[str, Any]:
        return {
            "default_variable": {
                "name": ast.name,
                "default_value": str(ast.default_value),
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
            "slice": {
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
            "slice": {
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
        return {"append": {"waveforms": list(map(self.visit, ast.waveforms))}}

    def visit_record(self, ast: waveform.Record) -> Dict[str, Any]:
        return {"record": {"var": ast.var, "waveform": self.visit(ast.waveform)}}

    def visit_smooth(self, ast: waveform.Smooth) -> Dict[str, Any]:
        return {
            "smooth": {
                "waveform": self.visit(ast.waveform),
                "radius": self.scalar_encoder.visit(ast.radius),
                "kernel": ast.kernel.value,
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


class ProgramSerializer(ProgramVisitor):
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
                        "shape": shape,
                    }
                }
            case location.Square(shape, lattice_spacing):
                return {
                    "square": {
                        "lattice_spacing": self.visit(lattice_spacing),
                        "shape": shape,
                    }
                }
            case location.Honeycomb(shape, lattice_spacing):
                return {
                    "honeycomb": {
                        "lattice_spacing": self.visit(lattice_spacing),
                        "shape": shape,
                    }
                }
            case location.Triangular(shape, lattice_spacing):
                return {
                    "triangular": {
                        "lattice_spacing": self.visit(lattice_spacing),
                        "shape": shape,
                    }
                }
            case location.Lieb(shape, lattice_spacing):
                return {
                    "lieb": {
                        "lattice_spacing": self.visit(lattice_spacing),
                        "shape": shape,
                    }
                }
            case location.Kagome(shape, lattice_spacing):
                return {
                    "kagome": {
                        "lattice_spacing": self.visit(lattice_spacing),
                        "shape": shape,
                    }
                }
            case location.Rectangular(shape, lattice_spacing_x, lattice_spacing_y):
                return {
                    "rectangular": {
                        "lattice_spacing_x": self.visit(lattice_spacing_x),
                        "lattice_spacing_y": self.visit(lattice_spacing_y),
                        "shape": shape,
                    }
                }

    def visit_parallel_register(self, ast: location.ParallelRegister) -> Any:
        register_locations = [
            list(map(self.visit, loc)) for loc in ast.register_locations
        ]
        shift_vectors = [list(map(self.visit, loc)) for loc in ast.register_locations]
        return {
            "parallel_register": {
                "register_locations": register_locations,
                "register_filling": ast.register_filling,
                "shift_vectors": shift_vectors,
            }
        }

    def visit_sequence(self, ast: sequence.SequenceExpr) -> Any:
        match ast:
            case sequence.Sequence(pulses):
                return {
                    "sequence": {
                        "pulses": {k.value: self.visit(v) for k, v in pulses.items()}
                    }
                }
            case sequence.Append(sequences):
                return {"append": {"sequences": [self.visit(s) for s in sequences]}}
            case sequence.NamedSequence(sub_sequence, name):
                return {
                    "named_sequence": {
                        "name": name,
                        "sub_sequence": self.visit(sub_sequence),
                    }
                }
            case sequence.Slice(sub_sequence, interval):
                return {
                    "slice": {
                        "sequence": self.visit(sub_sequence),
                        "interval": self.scalar_serializer.visit(interval),
                    }
                }

    def visit_pulse(self, ast: pulse.PulseExpr) -> Any:
        match ast:
            case pulse.Pulse(fields):
                return {
                    "pulse": {
                        "fields": {k.value: self.visit(v) for k, v in fields.items()}
                    }
                }
            case pulse.Append(pulses):
                return {"append": {"pulses": [self.visit(p) for p in pulses]}}
            case pulse.NamedPulse(name, sub_pulse):
                return {
                    "named_pulse": {"name": name, "sub_pulse": self.visit(sub_pulse)}
                }
            case pulse.Slice(sub_pulse, interval):
                return {
                    "slice": {
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


class BloqadeIRSerializer(json.JSONEncoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.program_serializer = ProgramSerializer()
        self.waveform_serializer = WaveformSerializer()
        self.scalar_serializer = ScalarSerilaizer()
        self.bloqade_seq_types = (
            location.AtomArrangement,
            location.ParallelRegister,
            program.Program,
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
