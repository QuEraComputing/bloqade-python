from enum import Enum

class TimeSeriesType(str, Enum):
    PiecewiseLinear = "piecewise_linear"
    PiecewiseConstant = "piecewise_constant"
    

class ToQuEra:

    def quera(self, *args, **kwargs):
        return NotImplemented