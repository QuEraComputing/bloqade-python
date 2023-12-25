from functools import reduce
from bloqade.ir.visitor import BloqadeIRVisitor
import bloqade.ir.control.waveform as waveform
import numpy as np


def concat(lhs: waveform.Waveform, rhs: waveform.Waveform) -> waveform.Waveform:
    return lhs.append(rhs)


class NormalizeWaveformPython(BloqadeIRVisitor):
    def visit_waveform_Sample(self, node: waveform.Sample):
        times, values = node.samples()

        durations = np.diff(times)

        if node.interpolation is waveform.Interpolation.Constant:
            segments = [waveform.Constant(*args) for args in zip(values, durations)]
        elif node.interpolation is waveform.Interpolation.Linear:
            segments = [
                waveform.Linear(*args)
                for args in zip(values[:-1], values[1:], durations)
            ]

        return reduce(concat, segments)
