from .base import Task, Batch, JSONInterface
from bloqade.submission.ir.task_specification import QuEraTaskSpecification
from bloqade.submission.quera import QuEraBackend
from typing import List


class QuEraTask(Task, JSONInterface):
    quera: QuEraBackend
    task_specification: QuEraTaskSpecification


class QuEraBatch(Batch, JSONInterface):
    futures: List[QuEraTask]
