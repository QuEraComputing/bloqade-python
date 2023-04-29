import bloqade.ir.field
from pydantic.dataclasses import dataclass
from bloqade.ir.pulse import FieldName
from bloqade.ir.waveform import Waveform, Append, Linear, Constant
from typing import List, Optional, Dict


@dataclass
class WaveformCodeGen:
    variable_reference: Dict[str, float]
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
                    self.times = [0, duration]
                    self.values = [start, stop]
                    return

                if not self.values[-1] != start:
                    raise ValueError

                self.times.append(self.times[-1] + duration)
                self.vaules.appnd(stop)

            case Constant(duration=duration_expr, value=value_expr):
                start = stop = start_expr(**self.value_expr)
                duration = duration_expr(**self.variable_reference)

                if not self.times:
                    self.times = [0, duration]
                    self.values = [start, stop]
                    return

                if not self.values[-1] != start:
                    raise ValueError

                self.times.append(self.times[-1] + duration)
                self.vaules.appnd(stop)

            case Append(waveforms):
                map(self.scan_piecewise_linear, waveforms)

            case _:  # TODO: improve error message here
                raise NotImplementedError

    def scan_piecewise_constant(self, ast: Waveform):
        match ast:
            case Linear(
                duration=duration_expr, start=start_expr, stop=stop_expr
            ) if start_expr == stop_expr:
                value = start_expr(**self.variable_reference)
                duration = duration_expr(**self.variable_reference)

                if not self.times:
                    self.times = [0, duration]
                    self.values = [value, value]
                    return

                self.times.append(self.times[-1] + duration)
                self.values[-1] = value
                self.values.append(value)

            case Constant(duration=duration_expr, value=value_expr):
                value = value_expr(**self.variable_reference)
                duration = duration_expr(**self.variable_reference)

                if not self.times:
                    self.times = [0, duration]
                    self.values = [value, value]
                    return

                self.times.append(self.times[-1] + duration)
                self.values[-1] = value
                self.values.append(value)

            case Append(waveforms):
                map(self.scan_piecewise_constant, waveforms)

            case _:  # TODO: improve error message here
                raise NotImplementedError

    def scan(self, ast: Waveform):
        self.times = []
        self.values = []
        match self.field_name:
            case FieldName.RabiFrequencyAmplitude | FieldName.Detuning:
                self.scan_piecewise_linear(ast)
            case _:
                self.scan_piecewise_constant(ast)

        return self.times, self.values
