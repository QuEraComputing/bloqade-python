from pydantic.dataclasses import dataclass
from bloqade.ir.pulse import FieldName
from bloqade.ir.waveform import Waveform, Append, Linear, Constant
from bloqade.codegen.hardware.base import BaseCodeGen
from typing import List, Optional, Tuple


@dataclass
class WaveformCodeGen(BaseCodeGen):
    field_name: Optional[FieldName] = None
    times: Optional[List[float]] = None
    values: Optional[List[float]] = None

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

                if self.values[-1] != start:
                    raise ValueError

                self.times.append(self.times[-1] + duration)
                self.values.append(stop)

            case Constant(duration=duration_expr, value=value_expr):
                start = stop = value_expr(**self.variable_reference)
                duration = duration_expr(**self.variable_reference)

                if not self.times:
                    self.times = [0, duration]
                    self.values = [start, stop]
                    return

                if self.values[-1] != start:
                    raise ValueError

                self.times.append(self.times[-1] + duration)
                self.values.append(stop)

            case Append(waveforms):
                for waveform in waveforms:
                    self.scan_piecewise_linear(waveform)

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
                for waveform in waveforms:
                    self.scan_piecewise_constant(waveform)

            case _:  # TODO: improve error message here
                raise NotImplementedError

    def scan(self, ast: Waveform):
        print(self.field_name)
        match self.field_name:
            case FieldName.RabiFrequencyAmplitude:
                print('amplitude')
                self.scan_piecewise_linear(ast)
            case FieldName.RabiFrequencyPhase:
                print('phase')
                self.scan_piecewise_constant(ast)
            case FieldName.Detuning:
                print('detuning')
                self.scan_piecewise_linear(ast)


    def emit(self, ast: Waveform) -> Tuple[List[float], List[float]]:
        self.times = []
        self.values = []
        self.scan(ast)
        return self.times, self.values