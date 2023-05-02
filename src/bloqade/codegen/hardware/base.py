from pydantic.dataclasses import dataclass
from typing import Dict


@dataclass
class BaseCodeGen:
    n_atoms: int
    assignments: Dict[str, float]
