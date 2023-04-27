from enum import Enum
from bloqade.ir.field import FieldName
from typing import Dict, Optional

class TimeSeriesType(str, Enum):
    PiecewiseLinear = "piecewise_linear"
    PiecewiseConstant = "piecewise_constant"
    

class ToQuEra:
    
    def quera(self):
        raise NotImplementedError(f"QuEra AHS feature doesn't support {self.__class__}")