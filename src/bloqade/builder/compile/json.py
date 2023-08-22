from typing import Any, Dict, Type
from ...codegen.common.json import BloqadeIRSerializer, BloqadeIRDeserializer
from ..start import ProgramStart
from ..sequence_builder import SequenceBuilder

# from ..base import Builder
from ..spatial import Location, Scale, Var, Uniform
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
from ..field import Detuning, Rabi, RabiAmplitude, RabiPhase
from ..coupling import Rydberg, Hyperfine
from ..parallelize import Parallelize, ParallelizeFlatten
from ..assign import Assign, BatchAssign
from ..flatten import Flatten
from ..backend import bloqade
from ..backend import braket
from ..backend import quera


class BuilderSerializer(BloqadeIRSerializer):
    def default(self, obj):
        def camel_to_snake(name: str) -> str:
            return "".join("_" + c.lower() if c.isupper() else c for c in name).lstrip(
                "_"
            )

        if isinstance(obj, ProgramStart) and type(obj) is ProgramStart:
            return "program_start"

        match obj:
            case braket.Aquila(parent):
                return {"braket_aquila": {"parent": parent}}
            case braket.BraketEmulator(parent):
                return {"braket_simu": {"parent": parent}}
            case quera.Aquila(parent):
                return {"quera_aquila": {"parent": parent}}
            case quera.Gemini(parent):
                return {"quera_gemini": {"parent": parent}}
            case bloqade.BloqadePython(parent):
                return {"bloqade_python": {"parent": parent}}
            case bloqade.BloqadeJulia(parent):
                return {"bloqade_julia": {"parent": parent}}
            case braket.BraketDeviceRoute(parent) | quera.QuEraDeviceRoute(
                parent
            ) | bloqade.BloqadeDeviceRoute(parent) | braket.BraketService(
                parent
            ) | quera.QuEraService(
                parent
            ) | bloqade.BloqadeService(
                parent
            ):
                return {camel_to_snake(obj.__class__.__name__): {"parent": parent}}
            case Parallelize(cluster_spacing, parent):
                return {
                    "parallelize": {"cluster_spacing": cluster_spacing},
                    "parent": parent,
                }
            case ParallelizeFlatten(cluster_spacing, parent):
                return {
                    "parallelize_flatten": {"cluster_spacing": cluster_spacing},
                    "parent": parent,
                }
            case SequenceBuilder(sequence, parent):
                return {
                    "sequence_builder": {
                        "sequence": self.default(sequence),
                        "parent": self.default(parent),
                    }
                }
            case Assign(assignments, parent) | BatchAssign(assignments, parent):
                return {
                    camel_to_snake(obj.__class__.__name__): {
                        "assignments": assignments,
                        "parent": parent,
                    }
                }
            case Flatten(order, parent):
                return {"flatten": {"order": order, "parent": parent}}
            case Constant(value, duration, parent):
                return {
                    "constant": {
                        "value": value,
                        "duration": duration,
                        "parent": parent,
                    }
                }
            case Linear(start, stop, duration, parent):
                return {
                    "linear": {
                        "start": start,
                        "stop": stop,
                        "duration": duration,
                        "parent": parent,
                    }
                }
            case Poly(coeffs, duration, parent):
                return {
                    "poly": {
                        "coeffs": coeffs,
                        "duration": duration,
                        "parent": parent,
                    }
                }
            case Fn():
                raise ValueError(
                    "Bloqade does not support serialization of Python code."
                )
            case Apply(wf, parent):
                return {"apply": {"wf": wf, "parent": parent}}
            case Slice(None, stop, parent):
                return {
                    "slice": {
                        "stop": stop,
                        "parent": parent,
                    }
                }
            case Slice(start, None, parent):
                return {
                    "slice": {
                        "start": start,
                        "parent": parent,
                    }
                }
            case Slice(start, stop, parent):
                return {
                    "slice": {
                        "start": start,
                        "stop": stop,
                        "parent": parent,
                    }
                }
            case Record(name, parent):
                return {
                    "record": {
                        "name": name,
                        "parent": parent,
                    }
                }
            case Sample(dt, interpolation, parent):
                return {
                    "sample": {
                        "dt": dt,
                        "interpolation": interpolation,
                        "parent": parent,
                    }
                }
            case PiecewiseLinear(durations, values, parent):
                return {
                    "piecewise_linear": {
                        "durations": durations,
                        "values": values,
                        "parent": parent,
                    }
                }
            case PiecewiseConstant(durations, values, parent):
                return {
                    "piecewise_constant": {
                        "durations": durations,
                        "values": values,
                        "parent": parent,
                    }
                }
            case Location(label, parent):
                return {
                    "location": {
                        "label": label,
                        "parent": parent,
                    }
                }
            case Scale(value, parent):
                return {
                    "scale": {
                        "value": value,
                        "parent": parent,
                    }
                }
            case Var(name, parent):
                return {"Var": {"name": name, "parent": parent}}
            case Uniform(parent):
                return {"uniform": {"parent": parent}}
            case Detuning(parent) | RabiAmplitude(parent) | RabiPhase(parent) | Rabi(
                parent
            ) | Hyperfine(parent) | Rydberg(parent):
                return {camel_to_snake(obj.__class__.__name__): {"parent": parent}}
            case _:
                return super().default(obj)


class BuilderDeserializer(BloqadeIRDeserializer):
    methods: Dict[str, Type] = {
        "rydberg": Rydberg,
        "hyperfine": Hyperfine,
        "detuning": Detuning,
        "rabi": Rabi,
        "rabi_amplitude": RabiAmplitude,
        "rabi_phase": RabiPhase,
        "var": Var,
        "scale": Scale,
        "location": Location,
        "uniform": Uniform,
        "piecewise_constant": PiecewiseConstant,
        "piecewise_linear": PiecewiseLinear,
        "sample": Sample,
        "record": Record,
        "slice": Slice,
        "apply": Apply,
        "poly": Poly,
        "linear": Linear,
        "constant": Constant,
        "flatten": Flatten,
        "parallelize": Parallelize,
        "parallelize_flatten": ParallelizeFlatten,
        "sequence_builder": SequenceBuilder,
        "assign": Assign,
        "batch_assign": BatchAssign,
        "bloqade_python": bloqade.BloqadePython,
        "bloqade_julia": bloqade.BloqadeJulia,
        "bloqade_device_route": bloqade.BloqadeDeviceRoute,
        "bloqade_service": bloqade.BloqadeService,
        "braket_device_route": braket.BraketDeviceRoute,
        "braket_service": braket.BraketService,
        "braket_aquila": braket.Aquila,
        "braket_simu": braket.BraketEmulator,
        "quera_device_route": quera.QuEraDeviceRoute,
        "quera_service": quera.QuEraService,
        "quera_aquila": quera.Aquila,
        "quera_gemini": quera.Gemini,
    }

    def object_hook(self, obj: Dict[str, Any]):
        match obj:
            case str("program_start"):
                return ProgramStart(None)
            case dict([(str(head), dict(options))]):
                if head in self.methods:
                    return self.methods[head](**options)
                else:
                    super().object_hook(obj)
            case _:
                raise NotImplementedError(f"Missing implementation for {obj}")
