from functools import reduce
from bloqade.ir.visitor.waveform import WaveformVisitor
import bloqade.ir.control.waveform as waveform
import numpy as np


def concat(lhs: waveform.Waveform, rhs: waveform.Waveform) -> waveform.Waveform:
    return lhs.append(rhs)


class NormalizeWaveformPython(WaveformVisitor):
    def visit_constant(self, ast: waveform.Constant):
        return ast

    def visit_linear(self, ast: waveform.Linear):
        return ast

    def visit_poly(self, ast: waveform.Poly):
        return ast

    def visit_python_fn(self, ast: waveform.PythonFn):
        return ast

    def visit_add(self, ast: waveform.Add):
        return self.visit(ast.left).append(self.visit(ast.right))

    def visit_append(self, ast: waveform.Append):
        return reduce(concat, map(self.visit, ast.waveforms))

    def visit_negative(self, ast: waveform.Negative):
        return -self.visit(ast.waveform)

    def visit_scale(self, ast: waveform.Scale):
        return self.visit(ast.waveform) * ast.scalar

    def visit_slice(self, ast: waveform.Slice):
        wf = self.visit(ast.waveform)
        return wf[ast.interval.start : ast.interval.stop]

    def visit_sample(self, ast: waveform.Sample):
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
