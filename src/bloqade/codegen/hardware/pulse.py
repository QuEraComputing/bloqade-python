import bloqade.ir.pulse import PulseBase
from pydantic.dataclasses import dataclass
from bloqade.ir.sequence import LevelCoupling
from bloqade.codegen.hardware.field import FieldCodeGen
from typing import Optional


@dataclass
class PulseCodeGen(FieldCodeGen):
    level_coupling: Optional[LevelCoupling] = None
    
    def scan(self, ast: PulseBase):
        raise NotImplementedError
            
    def emit(self, ast: PulseBase):
        raise NotImplementedError
    