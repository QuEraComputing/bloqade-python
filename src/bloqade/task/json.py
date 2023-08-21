from collections import OrderedDict
from decimal import Decimal
from bloqade.builder.compile.braket_simulator import BraketEmulatorTaskData
from bloqade.submission.braket import BraketBackend
from bloqade.submission.ir.parallel import ParallelDecoder

from bloqade.submission.ir.task_results import QuEraTaskResults
from bloqade.submission.ir.task_specification import QuEraTaskSpecification
from bloqade.submission.mock import DumbMockBackend
from bloqade.submission.quera import QuEraBackend
from .braket import BraketTask
from .quera import QuEraTask
from .batch import RemoteBatch, LocalBatch
from typing import Type, Dict, Any
from .braket_simulator import BraketEmulatorTask
from bloqade.builder.compile.quera import QuEraTaskData
import json


class BatchSerializer(json.JSONEncoder):
    def default(self, obj):
        match obj:
            case RemoteBatch(tasks, name):
                return {
                    "remote_batch": {
                        "name": name,
                        "tasks": [(k, v) for k, v in tasks.items()],
                    }
                }

            case LocalBatch(tasks, name):
                return {
                    "local_batch": {
                        "name": name,
                        "tasks": [(k, v) for k, v in tasks.items()],
                    }
                }

            case QuEraTask(task_id, QuEraBackend(), task_data, None):
                # skip saving data for now
                return {
                    "quera_task": {
                        "task_id": task_id,
                        "backend": "quera_backend",
                        "task_data": task_data,
                    }
                }
            case QuEraTask(task_id, QuEraBackend(), task_data, task_result_ir):
                # skip saving data for now
                return {
                    "quera_task": {
                        "task_id": task_id,
                        "task_data": task_data,
                        "backend": "quera_backend",
                        "task_result_ir": task_result_ir.dict(
                            exclude_none=True, by_alias=True
                        ),
                    }
                }
            case QuEraTask(task_id, DumbMockBackend(), task_data, None):
                # skip saving data for now
                return {
                    "quera_task": {
                        "task_id": task_id,
                        "backend": "mock_backend",
                        "task_data": task_data,
                    }
                }
            case QuEraTask(task_id, DumbMockBackend(), task_data, task_result_ir):
                # skip saving data for now
                return {
                    "quera_task": {
                        "task_id": task_id,
                        "task_data": task_data,
                        "backend": "mock_backend",
                        "task_result_ir": task_result_ir.dict(
                            exclude_none=True, by_alias=True
                        ),
                    }
                }
            case BraketTask(task_id, task_data, None):
                # skip saving data for now
                return {"braket_task": {"task_id": task_id, "task_data": task_data}}
            case BraketTask(task_id, task_data, _, task_result_ir):
                # skip saving data for now
                return {
                    "braket_task": {
                        "task_id": task_id,
                        "task_data": task_data,
                        "task_result_ir": task_result_ir.json(
                            exclude_none=True, by_alias=True
                        ),
                    }
                }
            case BraketEmulatorTask(task_data, None):
                return {
                    "braket_emulator_task": {
                        "task_data": task_data,
                    }
                }
            case BraketEmulatorTask(task_data, task_result_ir):
                return {
                    "braket_emulator_task": {
                        "task_data": task_data,
                        "task_result_ir": task_result_ir.dict(
                            exclude_none=True, by_alias=True
                        ),
                    }
                }
            case QuEraTaskData(task_ir, metadata, None):
                return {
                    "quera_task_data": {
                        "task_ir": task_ir.dict(by_alias=True, exclude_none=True),
                        "metadata": metadata,
                    }
                }
            case QuEraTaskData(task_ir, metadata, parallel_decoder):
                return {
                    "quera_task_data": {
                        "task_ir": task_ir.dict(by_alias=True, exclude_none=True),
                        "metadata": metadata,
                        "parallel_decoder": parallel_decoder.dict(
                            by_alias=True, exclude_none=True
                        ),
                    }
                }
            case BraketEmulatorTaskData(task_ir, metadata):
                return {
                    "braket_emulator_task_data": {
                        "task_ir": task_ir.dict(by_alias=True, exclude_none=True),
                        "metadata": metadata,
                    }
                }
            case Decimal():  # needed for dumping BaseModel's with json module
                return str(obj)
            case _:
                return super().default(obj)


class BatchDeserializer:
    methods_batch: Dict[str, Type] = {
        "remote": RemoteBatch,
        "local": LocalBatch,
    }

    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs

    def object_hook(self, obj: Dict[str, Any]):
        match obj:
            case {"remote_batch": {"name": name, "tasks": tasks}}:
                return RemoteBatch(OrderedDict(tasks), name)
            case {"local_batch": {"name": name, "tasks": tasks}}:
                return LocalBatch(OrderedDict(tasks), name)
            case {
                "quera_task": {
                    "task_id": task_id,
                    "task_data": task_data,
                    "backend": "quera_backend",
                }
            }:
                return QuEraTask(
                    task_data,
                    task_id=task_id,
                    backend=QuEraBackend(*self._args, **self._kwargs),
                )
            case {
                "quera_task": {
                    "task_id": task_id,
                    "task_data": task_data,
                    "backend": "mock_backend",
                }
            }:
                return QuEraTask(
                    task_data,
                    task_id=task_id,
                    backend=DumbMockBackend(*self._args, **self._kwargs),
                )
            case {"braket_task": {"task_id": task_id, "task_data": task_data}}:
                return BraketTask(
                    task_data,
                    task_id=task_id,
                    backend=BraketBackend(*self._args, **self._kwargs),
                )
            case {"braket_emulator_task": {"task_data": task_data}}:
                return BraketEmulatorTask(
                    task_data,
                )
            case {
                "quera_task": {
                    "task_id": task_id,
                    "backend": "quera_backend",
                    "task_data": task_data,
                    "task_result_ir": task_result_ir,
                }
            }:
                task = QuEraTask(
                    task_data,
                    task_id=task_id,
                    backend=QuEraBackend(*self._args, **self._kwargs),
                )
                task.task_result_ir = QuEraTaskResults(**task_result_ir)
                return task
            case {
                "quera_task": {
                    "task_id": task_id,
                    "backend": "mock_backend",
                    "task_data": task_data,
                    "task_result_ir": task_result_ir,
                }
            }:
                task = QuEraTask(
                    task_data,
                    task_id=task_id,
                    backend=DumbMockBackend(*self._args, **self._kwargs),
                )
                task.task_result_ir = QuEraTaskResults(**task_result_ir)
                return task
            case {
                "braket_task": {
                    "task_id": task_id,
                    "task_data": task_data,
                    "task_result_ir": task_result_ir,
                }
            }:
                task = BraketTask(
                    task_data,
                    task_id=task_id,
                    backend=BraketBackend(*self._args, **self._kwargs),
                )
                task.task_result_ir = QuEraTaskResults(**task_result_ir)
                return task
            case {
                "braket_emulator_task": {
                    "task_data": task_data,
                    "task_result_ir": task_result_ir,
                }
            }:
                task = BraketEmulatorTask(
                    task_data,
                )
                task.task_result_ir = QuEraTaskResults(**task_result_ir)
                return task
            case {"quera_task_data": {"task_ir": task_ir_dict, "metadata": metadata}}:
                task_ir = QuEraTaskSpecification(**task_ir_dict)
                return QuEraTaskData(task_ir, metadata)
            case {
                "quera_task_data": {
                    "task_ir": task_ir_dict,
                    "metadata": metadata,
                    "parallel_decoder": parallel_decoder_dict,
                }
            }:
                task_ir = QuEraTaskSpecification(**task_ir_dict)
                parallel_decoder = ParallelDecoder(**parallel_decoder_dict)
                return QuEraTaskData(task_ir, metadata, parallel_decoder)
            case {
                "braket_emulator_task_data": {
                    "task_ir": task_ir_dict,
                    "metadata": metadata,
                }
            }:
                task_ir = QuEraTaskSpecification(**task_ir_dict)
                return BraketEmulatorTaskData(task_ir, metadata)
            case _:
                return obj
