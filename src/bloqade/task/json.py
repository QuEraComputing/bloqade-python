from collections import OrderedDict
from decimal import Decimal
from bloqade.submission.braket import BraketBackend
from bloqade.submission.ir.braket import BraketTaskSpecification
from bloqade.submission.ir.parallel import ParallelDecoder
from bloqade.submission.ir.task_results import QuEraTaskResults
from bloqade.submission.ir.task_specification import QuEraTaskSpecification
from bloqade.submission.mock import DumbMockBackend
from bloqade.submission.quera import QuEraBackend
from .braket import BraketTask
from .quera import QuEraTask
from .batch import RemoteBatch, LocalBatch
from typing import TextIO, Dict, Any, Union
from .braket_simulator import BraketEmulatorTask
import json


class BatchSerializer(json.JSONEncoder):
    def default(self, obj):
        match obj:
            case RemoteBatch(_, tasks, name):
                return {
                    "remote_batch": {
                        "batch": None,
                        "name": name,
                        "tasks": [(k, v) for k, v in tasks.items()],
                    }
                }

            case LocalBatch(_, tasks, name):  # skip program for now
                return {
                    "local_batch": {
                        "batch": None,
                        "name": name,
                        "tasks": [(k, v) for k, v in tasks.items()],
                    }
                }

            case QuEraTask(
                task_id,
                backend,
                task_ir,
                metadata,
                parallel_decoder,
                task_result_ir,
            ):
                return {
                    "quera_task": {
                        "backend": backend,
                        "task_id": task_id,
                        "parallel_decoder": parallel_decoder,
                        "task_result_ir": task_result_ir,
                        "task_ir": task_ir,
                        "metadata": metadata,
                    }
                }

            case BraketTask(
                task_id,
                backend,
                task_ir,
                metadata,
                parallel_decoder,
                task_result_ir,
            ):
                return {
                    "braket_task": {
                        "task_id": task_id,
                        "backend": backend,
                        "parallel_decoder": parallel_decoder,
                        "task_result_ir": task_result_ir,
                        "task_ir": task_ir,
                        "metadata": metadata,
                    }
                }
            case BraketEmulatorTask(task_ir, metadata, task_result_ir):
                return {
                    "braket_emulator_task": {
                        "task_ir": task_ir,
                        "metadata": metadata,
                        "task_result_ir": task_result_ir,
                    }
                }
            case QuEraBackend() as quera_backend:
                return {
                    "quera_backend": quera_backend.dict(
                        exclude=set(["access_key", "secret_key", "session_token"])
                    )
                }
            case DumbMockBackend() as dumb_mock_backend:
                return {"mock_backend": dumb_mock_backend.dict()}
            case BraketBackend() as backend:
                return {"braket_backend": backend.dict()}
            case QuEraTaskSpecification() as task_ir:
                return {"quera_task_specification": task_ir.dict(by_alias=True)}
            case BraketTaskSpecification() as task_ir:
                return {"braket_task_specification": task_ir.dict()}
            case ParallelDecoder() as parallel_decoder:
                return {"parallel_decoder": parallel_decoder.dict()}
            case QuEraTaskResults() as task_result_ir:
                return {"task_result_ir": task_result_ir.dict()}
            case Decimal():  # needed for dumping BaseModel's with json module
                return str(obj)
            case _:
                return super().default(obj)


class BatchDeserializer:
    constructor_mapping = {
        "remote_batch": RemoteBatch,
        "local_batch": LocalBatch,
        "quera_task": QuEraTask,
        "braket_task": BraketTask,
        "braket_emulator_task": BraketEmulatorTask,
        "quera_task_specification": QuEraTaskSpecification,
        "braket_task_specification": BraketTaskSpecification,
        "parallel_decoder": ParallelDecoder,
        "task_result_ir": QuEraTaskResults,
        "quera_backend": QuEraBackend,
        "mock_backend": DumbMockBackend,
        "braket_backend": BraketBackend,
    }

    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs

    def object_hook(self, obj: Dict[str, Any]):
        if len(obj) == 1:
            ((head, body),) = obj.items()
            if head in self.constructor_mapping:
                if "tasks" in body:
                    body["tasks"] = OrderedDict(body["tasks"])

                return self.constructor_mapping[head](**body)

        return obj


def save_batch(
    filename_or_io: Union[str, TextIO], batch: Union[RemoteBatch, LocalBatch]
) -> None:
    """save batch to json file or string io

    Args:
        filename_or_io (Union[str, TextIO]): filename or file object pointing to
        json file.
        batch (Union[RemoteBatch, LocalBatch]): batch object to save.
    """
    if isinstance(filename_or_io, str):
        with open(filename_or_io, "w") as f:
            json.dump(batch, f, cls=BatchSerializer)
    else:
        json.dump(batch, filename_or_io, cls=BatchSerializer)


def load_batch(
    filename_or_io: Union[str, TextIO], *backend_args, **backend_kwargs
) -> Union[RemoteBatch, LocalBatch]:
    """load batch from json file or string io to batch object

    Args:
        filename_or_io (Union[str, TextIO]): filename or file object pointing to
        json file.
        *backend_args: args to pass to backend construction.
        **backend_kwargs: kwargs to pass to backend construction.

    Returns:
        Union[RemoteBatch, LocalBatch]: the resulting batch object

    Note:
        The backend args are not always required for `LocalBatch` objects, but
        for `RemoteBatch` objects they are required.
    """
    deserializer = BatchDeserializer(*backend_args, **backend_kwargs)
    if isinstance(filename_or_io, str):
        with open(filename_or_io, "r") as f:
            return json.load(f, object_hook=deserializer.object_hook)
    else:
        return json.load(filename_or_io, object_hook=deserializer.object_hook)
