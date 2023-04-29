from pydantic.dataclasses import dataclass
from bloqade.ir.field import Field

from typing import List, Optional
from bloqade.codegen.hardware.spatial_modulation import SpatialModulationCodeGen


class TimeSeriesType(str, Enum):
    PiecewiseLinear = "piecewise_linear"
    PiecewiseConstant = "piecewise_constant"

@dataclass
class FieldCodeGen(SpatialModulationCodeGen):
    
    def scan(self, ast: Field):
        raise NotImplementedError
            
    def emit(self, ast: Field):
        raise NotImplementedError

    
    

