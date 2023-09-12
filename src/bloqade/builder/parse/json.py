from typing import Any, Dict, TextIO, Type, Union
from bloqade.builder.base import Builder
from bloqade.codegen.common.json import BloqadeIRSerializer, BloqadeIRDeserializer
from bloqade.builder.start import ProgramStart
from bloqade.builder.sequence_builder import SequenceBuilder

# from bloqade.builder.base import Builder
from bloqade.builder.backend.bloqade import BloqadeDeviceRoute, BloqadeService
from bloqade.builder.backend.braket import BraketDeviceRoute, BraketService
from bloqade.builder.backend.quera import QuEraDeviceRoute, QuEraService
from bloqade.builder.spatial import Location, Scale, Var, Uniform
from bloqade.builder.waveform import (
    Linear,
    Constant,
    Poly,
    Apply,
    Slice,
    Record,
    Sample,
    PiecewiseLinear,
    PiecewiseConstant,
)
from bloqade.builder.field import Detuning, Rabi, RabiAmplitude, RabiPhase
from bloqade.builder.coupling import Rydberg, Hyperfine
from bloqade.builder.parallelize import Parallelize
from bloqade.builder.assign import Assign, BatchAssign
from bloqade.builder.flatten import Flatten


class BuilderSerializer(BloqadeIRSerializer):
    types = set(
        [
            ProgramStart,
            SequenceBuilder,
            BloqadeDeviceRoute,
            BloqadeService,
            BraketDeviceRoute,
            BraketService,
            QuEraDeviceRoute,
            QuEraService,
            Location,
            Scale,
            Var,
            Uniform,
            Linear,
            Constant,
            Poly,
            Apply,
            Slice,
            Record,
            Sample,
            PiecewiseLinear,
            PiecewiseConstant,
            Detuning,
            Rabi,
            RabiAmplitude,
            RabiPhase,
            Rydberg,
            Hyperfine,
            Parallelize,
            Assign,
            BatchAssign,
            Flatten,
        ]
    )

    def default(self, obj):
        if isinstance(obj, ProgramStart) and type(obj) is ProgramStart:
            return "program_start"

        if type(obj) in self.types:
            return {
                type(obj).__name__: {
                    arg: getattr(obj, arg) for arg in obj.__match_args__
                }
            }


class BuilderDeserializer(BloqadeIRDeserializer):
    methods: Dict[str, Type] = {
        "ProgramStart": ProgramStart,
        "SequenceBuilder": SequenceBuilder,
        "BloqadeDeviceRoute": BloqadeDeviceRoute,
        "BloqadeService": BloqadeService,
        "BraketDeviceRoute": BraketDeviceRoute,
        "BraketService": BraketService,
        "QuEraDeviceRoute": QuEraDeviceRoute,
        "QuEraService": QuEraService,
        "Location": Location,
        "Scale": Scale,
        "Var": Var,
        "Uniform": Uniform,
        "Linear": Linear,
        "Constant": Constant,
        "Poly": Poly,
        "Apply": Apply,
        "Slice": Slice,
        "Record": Record,
        "Sample": Sample,
        "PiecewiseLinear": PiecewiseLinear,
        "PiecewiseConstant": PiecewiseConstant,
        "Detuning": Detuning,
        "Rabi": Rabi,
        "RabiAmplitude": RabiAmplitude,
        "RabiPhase": RabiPhase,
        "Rydberg": Rydberg,
        "Hyperfine": Hyperfine,
        "Parallelize": Parallelize,
        "Assign": Assign,
        "BatchAssign": BatchAssign,
        "Flatten": Flatten,
    }

    def object_hook(self, obj: Dict[str, Any]):
        if isinstance(obj, dict) and len(obj) == 1:
            ((head, options),) = obj.items()
            if head in self.methods:
                return self.methods[head](**options)
        elif obj == "program_start":
            return ProgramStart(None)

        return super().object_hook(obj)


def load_program(filename_or_io: Union[str, TextIO]) -> Builder:
    import json

    if isinstance(filename_or_io, str):
        with open(filename_or_io, "r") as f:
            return json.load(f, object_hook=BuilderDeserializer().object_hook)
    else:
        return json.load(filename_or_io, object_hook=BuilderDeserializer().object_hook)


def save_program(filename_or_io: Union[str, TextIO], program: Builder) -> None:
    import json

    if isinstance(filename_or_io, str):
        with open(filename_or_io, "w") as f:
            json.dump(program, f, cls=BuilderSerializer)
    else:
        json.dump(program, filename_or_io, cls=BuilderSerializer)
