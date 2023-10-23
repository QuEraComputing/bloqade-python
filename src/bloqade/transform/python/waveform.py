from decimal import Decimal
from functools import reduce
from typing import Any
from bloqade.ir.control.waveform import (
    Add,
    AlignedWaveform,
    Append,
    Linear,
    Negative,
    Poly,
    PythonFn,
    Record,
    Sample,
    Scale,
    Slice,
)
from bloqade.ir.visitor.waveform import WaveformVisitor
import bloqade.ir.control.waveform as waveform
import numpy as np


def concat(lhs: waveform.Waveform, rhs: waveform.Waveform) -> waveform.Waveform:
    return lhs.append(rhs)


class NormalizeWaveformPython(WaveformVisitor):
    def visit_constant(self, ast: waveform.Constant) -> Any:
        return ast

    def visit_linear(self, ast: Linear) -> Any:
        return ast

    def visit_poly(self, ast: Poly) -> Any:
        return ast

    def visit_python_fn(self, ast: PythonFn) -> Any:
        return ast

    def visit_add(self, ast: Add) -> Any:
        return self.visit(ast.left) + self.visit(ast.right)

    def visit_append(self, ast: Append) -> Any:
        return reduce(concat, map(self.visit, ast.waveforms))

    def visit_negative(self, ast: Negative) -> Any:
        return -self.visit(ast.waveform)

    def visit_scale(self, ast: Scale) -> Any:
        return self.visit(ast.waveform) * ast.scalar

    def visit_slice(self, ast: Slice) -> Any:
        wf = self.visit(ast.waveform)

        if not isinstance(wf, waveform.Append):
            start = ast.interval.start() if ast.interval.start is not None else Decimal(0)
            stop = ast.interval.stop() if ast.interval.stop is not None else wf.duration()

            durations = np.cumsum([0] + [wf.duration() for wf in wf.waveforms])

            i = np.searchsorted(durations, start)
            j = np.searchsorted(durations, stop)

            start = start - durations[i - 1]
            stop = stop - durations[j - 1]

            if i == j:
                return self.visit(wf.waveforms[i][start:stop])
            else:
                segments = [
                    self.visit(wf.waveforms[i][start:]),
                    *wf.waveforms[i + 1 : j],
                    self.visit(wf.waveforms[j][:stop]),
                ]

                return reduce(concat, segments)
        elif isinstance(wf, waveform.Slice):
            start = ast.interval.start() + wf.interval.start()
            stop = ast.interval.stop() + start
            
            return self.visit(wf.waveform[start:stop])
            
        else:
            return wf[ast.interval.start() : ast.interval.stop()]



    def visit_sample(self, ast: Sample) -> Any:
        times, values = ast.samples()

        durations = np.diff(times)

        if ast.interpolation is waveform.Interpolation.Constant:
            segments = [waveform.Constant(*args) for args in zip(values, durations)]
        elif ast.interpolation is waveform.Interpolation.Linear:
            segments = [
                waveform.Linear(*args)
                for args in zip(values[:-1], values[1:], durations)
            ]

        return reduce(concat, segments)
    