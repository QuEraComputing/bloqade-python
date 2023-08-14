from ...codegen.common.json import BloqadeIRSerializer
from ..start import ProgramStart
from ..sequence_builder import SequenceBuilder
from ..base import Builder
from ..spatial import Location, Scale, Var
from ..waveform import (
    Linear,
    Constant,
    Poly,
    Fn,
    Apply,
    Slice,
    Record,
    Sample,
    PiecewiseLinear,
    PiecewiseConstant,
)


class BuilderSerializer(BloqadeIRSerializer):
    def default(self, obj):
        match obj:
            case Constant(value, duration, parent):
                return {
                    "Constant": {
                        "value": self.default(value),
                        "duration": self.default(duration),
                        "parent": self.default(parent),
                    }
                }
            case Linear(start, stop, duration, parent):
                return {
                    "Linear": {
                        "start": self.default(start),
                        "stop": self.default(stop),
                        "duration": self.default(duration),
                        "parent": self.default(parent),
                    }
                }
            case Poly(coeffs, duration, parent):
                return {
                    "Poly": {
                        "coeffs": self.default(coeffs),
                        "duration": self.default(duration),
                        "parent": self.default(parent),
                    }
                }
            case Fn():
                raise ValueError(
                    "Bloqade does not support serialization of Python code."
                )
            case Apply(wf, parent):
                return {
                    "Apply": {"wf": self.default(wf), "parent": self.default(parent)}
                }
            case Slice(None, stop, parent):
                return {
                    "Slice": {
                        "stop": self.default(stop),
                        "parent": self.default(parent),
                    }
                }
            case Slice(start, None, parent):
                return {
                    "Slice": {
                        "start": self.default(start),
                        "parent": self.default(parent),
                    }
                }
            case Slice(start, stop, parent):
                return {
                    "Slice": {
                        "start": self.default(start),
                        "stop": self.default(stop),
                        "parent": self.default(parent),
                    }
                }
            case Record(name, parent):
                return {
                    "Record": {
                        "name": self.default(name),
                        "parent": self.default(parent),
                    }
                }
            case Sample(dt, interpolation, parent):
                return {
                    "Sample": {
                        "dt": self.default(dt),
                        "interpolation": self.default(interpolation),
                        "parent": self.default(parent),
                    }
                }
            case PiecewiseLinear(durations, values, parent):
                return {
                    "PiecewiseLinear": {
                        "durations": self.default(durations),
                        "values": self.default(values),
                        "parent": self.default(parent),
                    }
                }
            case PiecewiseConstant(durations, values, parent):
                return {
                    "PiecewiseConstant": {
                        "durations": self.default(durations),
                        "values": self.default(values),
                        "parent": self.default(parent),
                    }
                }
            case Location(label, parent):
                return {
                    "Location": {
                        "label": label,
                        "parent": self.default(parent),
                    }
                }
            case Scale(value, parent):
                return {
                    "Scale": {
                        "value": value,
                        "parent": self.default(parent),
                    }
                }
            case Var(name, parent):
                return {"Var": {"name": name, "parent": self.default(parent)}}
            case ProgramStart():
                return super().default(obj)
            case SequenceBuilder(sequence, parent):
                return {
                    "sequence_builder": {
                        "sequence": self.default(sequence),
                        "parent": self.default(parent),
                    }
                }
            case Builder(parent):  # default serialization implementation
                if parent is None:
                    return {obj.__class__.__name__: {}}
                else:
                    return {obj.__class__.__name__: {"parent": self.default(parent)}}
            case _:
                return super().default(obj)
