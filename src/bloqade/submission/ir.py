import braket.ir.ahs as braket_ir
from bloqade.submission.quera_api_client.ir.task_specification import (
    QuEraTaskSpecification,
)
from typing import Union
from pydantic import BaseModel


class BraketTaskSpecification(BaseModel):
    nshots: int
    program: braket_ir.Program


QuantumTaskIR = Union[QuEraTaskSpecification, BraketTaskSpecification]
