from collections import OrderedDict
from decimal import Decimal
from bloqade.submission.braket import BraketBackend
from bloqade.submission.ir.braket import BraketTaskSpecification
from bloqade.submission.ir.parallel import ParallelDecoder
from bloqade.submission.ir.task_results import QuEraTaskResults
from bloqade.submission.ir.task_specification import QuEraTaskSpecification
from bloqade.submission.mock import MockBackend
from bloqade.submission.quera import QuEraBackend
from .braket import BraketTask
from .quera import QuEraTask
from .batch import RemoteBatch, LocalBatch
from typing import TextIO, Dict, Any, Union
from .braket_simulator import BraketEmulatorTask
import json


class BatchSerializer(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        elif isinstance(obj, QuEraBackend):
            return {
                "quera_backend": obj.dict(
                    exclude=set(["access_key", "secret_key", "session_token"])
                )
            }
        elif isinstance(obj, MockBackend):
            return {"mock_backend": obj.dict()}
        elif isinstance(obj, BraketBackend):
            return {"braket_backend": obj.dict()}
        elif isinstance(obj, QuEraTaskSpecification):
            return {"quera_task_specification": obj.dict(by_alias=True)}
        elif isinstance(obj, BraketTaskSpecification):
            return {"braket_task_specification": obj.dict()}
        elif isinstance(obj, ParallelDecoder):
            return {"parallel_decoder": obj.dict()}
        elif isinstance(obj, QuEraTaskResults):
            return {"task_result_ir": obj.dict()}
        elif isinstance(obj, BraketTask):
            return {
                "braket_task": {
                    "task_id": obj.task_id,
                    "backend": obj.backend,
                    "parallel_decoder": obj.parallel_decoder,
                    "task_result_ir": obj.task_result_ir,
                    "task_ir": obj.task_ir,
                    "metadata": obj.metadata,
                }
            }
        elif isinstance(obj, BraketEmulatorTask):
            return {
                "braket_emulator_task": {
                    "task_ir": obj.task_ir,
                    "metadata": obj.metadata,
                    "task_result_ir": obj.task_result_ir,
                }
            }
        elif isinstance(obj, QuEraTask):
            return {
                "quera_task": {
                    "backend": obj.backend,
                    "task_id": obj.task_id,
                    "parallel_decoder": obj.parallel_decoder,
                    "task_result_ir": obj.task_result_ir,
                    "task_ir": obj.task_ir,
                    "metadata": obj.metadata,
                }
            }

        elif isinstance(obj, LocalBatch):
            return {
                "local_batch": {
                    "source": None,
                    "name": obj.name,
                    "tasks": [(k, v) for k, v in obj.tasks.items()],
                }
            }
        elif isinstance(obj, RemoteBatch):
            return {
                "remote_batch": {
                    "source": None,
                    "name": obj.name,
                    "tasks": [(k, v) for k, v in obj.tasks.items()],
                }
            }
        else:
            return obj


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
        "mock_backend": MockBackend,
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
                elif head in ["quera_backend", "braket_backend", "mock_backend"]:
                    body = {**body, **self._kwargs}

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
