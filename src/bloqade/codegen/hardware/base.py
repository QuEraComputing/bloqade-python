from pydantic.dataclasses import dataclass
from typing import Dict, Union


@dataclass
class BaseCodeGen:
    n_atoms: int
    assignments: Union[None, Dict[str, float]]
