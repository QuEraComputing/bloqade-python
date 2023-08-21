from .braket import BraketTask
from .quera import QuEraTask
from .batch import RemoteBatch, LocalBatch
from typing import Type, Dict, Any
from .braket_simulator import BraketEmulatorTask
from bloqade.submission.ir.task_results import QuEraTaskResults
import json


class BatchSerializer(json.JSONEncoder):
    def default(self, obj):
        match obj:
            case RemoteBatch(tasks, name):
                return {"remote": {"name": name, "tasks": tasks}}

            case LocalBatch(tasks, name):
                return {"local": {"name": name, "tasks": tasks}}

            case QuEraTask(task_id, _, _, task_result_ir):
                # skip saving data for now
                return {
                    "task_id": task_id,
                    "task_data": "TASK_DATA",
                    "backend": "QuEra",
                    "task_result_ir": task_result_ir.json(
                        exclude_none=True, by_alias=True
                    ),
                }

            case BraketTask(task_id, _, _, task_result_ir):
                # skip saving data for now
                return {
                    "task_id": task_id,
                    "task_data": "TASK_DATA",
                    "backend": "Braket",
                    "task_result_ir": task_result_ir.json(
                        exclude_none=True, by_alias=True
                    ),
                }

            case BraketEmulatorTask(_, task_result_ir):
                return {
                    "task_data": "TASK_DATA",
                    "backend": "BraketEmulator",
                    "task_result_ir": task_result_ir.json(
                        exclude_none=True, by_alias=True
                    ),
                }

            case _:
                return super().default(obj)


class BatchDeserializer:
    methods_batch: Dict[str, Type] = {
        "remote": RemoteBatch,
        "local": LocalBatch,
    }

    def object_hook(self, obj: Dict[str, Any]):
        match obj:
            case dict([(str(head), dict(options))]):
                if head in self.methods_batch:
                    return self.methods[head](
                        name=options["name"], tasks=options["tasks"]
                    )

                else:
                    super().object_hook(obj)

            case {
                "task_data": _,
                "backend": backend,
                "task_result_ir": task_ir_string,
            }:
                tmp = BraketEmulatorTask(None)
                tmp.task_result_ir = QuEraTaskResults(**json.loads(task_ir_string))

                return tmp

            case {
                "task_id": task_id,
                "task_data": _,
                "backend": backend,
                "task_result_ir": task_ir_string,
            }:
                if backend == "QuEra":
                    tmp = QuEraTask(None, task_id=task_id)
                    tmp.task_result_ir = QuEraTaskResults(**json.loads(task_ir_string))
                    return tmp
                elif backend == "Braket":
                    tmp = BraketTask(None, task_id=task_id)
                    tmp.task_result_ir = QuEraTaskResults(**json.loads(task_ir_string))
                    return tmp
                else:
                    raise ValueError(f"backend {backend} is not recognized.")

            case _:
                raise NotImplementedError(f"Missing implementation for {obj}")


"""
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

"""
