from pydantic.dataclasses import dataclass
from bloqade.codegen.hardware.field import TimeSeriesType
from bloqade.ir.waveform import Waveform, Append, Linear, Constant
from typing import List, Optional

@dataclass
class WaveformCodeGen:
    field_name: Optional[FieldName] = None
    times: List[float] = []
    values: List[float] = []
    
    def scan_piecewise_linear(self, ast: Waveform):
        match ast:
            case Linear(duration=duration_expr, start=start_expr, stop=stop_expr):
                start = start_expr(**self.variable_reference)
                stop = stop_expr(**self.variable_reference)
                duration = duration_expr(**self.variable_reference)
                
                if not self.times:
                    self.times = [0,duration]                    
                    self.values = [start, stop]
                    return 
                
                if not self.values[-1] != start:
                    raise ValueError
                
                self.times.append(self.times[-1] + duration)
                self.vaules.appnd(stop)
            
            case Constant(duration=duration_expr, value=value_expr):
                start = start_expr(**self.variable_reference)
                stop = stop_expr(**self.variable_reference)
                duration = duration_expr(**self.variable_reference)
            
                if not self.times:
                    self.times = [0,duration]                    
                    self.values = [start, stop]
                    return 
                
                if not self.values[-1] != start:
                    raise ValueError
                
                self.times.append(self.times[-1] + duration)
                self.vaules.appnd(stop)
            
            case Append(waveforms):
                map(self.scan, waveforms)
            
            case _:
                raise NotImplementedError
            
    def scan_piecewise_constant(self, ast: Waveform):
        raise NotImplementedError
    
    def scan(self,ast: Waveform):
        match self.time_series_type:
            case TimeSeriesType.PiecewiseLinear:
                self.scan_piecewise_linear(ast)
            case TimeSeriesType.PiecewiseConstant:
                self.scan_piecewise_constant(ast)
                
    def emit(self, ast: Waveform):
        self.scan(ast)
