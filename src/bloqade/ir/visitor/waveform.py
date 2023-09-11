from bloqade.ir.control.waveform import (
    Waveform,
    AlignedWaveform,
    Linear,
    Constant,
    Poly,
    Smooth,
    Slice,
    Append,
    Negative,
    Scale,
    Add,
    Record,
    PythonFn,
    Sample,
)
from typing import Any


class WaveformVisitor:
    def visit_alligned(self, ast: AlignedWaveform) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for AlignedWaveform."
        )

    def visit_linear(self, ast: Linear) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for Linear."
        )

    def visit_constant(self, ast: Constant) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for Constant."
        )

    def visit_poly(self, ast: Poly) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for Poly."
        )

    def visit_smooth(self, ast: Smooth) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for Smooth."
        )

    def visit_slice(self, ast: Slice) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for Slice."
        )

    def visit_append(self, ast: Append) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for Append."
        )

    def visit_negative(self, ast: Negative) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for Negative."
        )

    def visit_scale(self, ast: Scale) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for Scale."
        )

    def visit_add(self, ast: Add) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for Add."
        )

    def visit_record(self, ast: Record) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for Record."
        )

    def visit_python_fn(self, ast: PythonFn) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for PythonFn."
        )

    def visit_sample(self, ast: Sample) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for Sample."
        )

    def visit(self, ast: Waveform):
        if isinstance(ast, Linear):
            return self.visit_linear(ast)
        elif isinstance(ast, Constant):
            return self.visit_constant(ast)
        elif isinstance(ast, PythonFn):
            return self.visit_python_fn(ast)
        elif isinstance(ast, Poly):
            return self.visit_poly(ast)
        elif isinstance(ast, Append):
            return self.visit_append(ast)
        elif isinstance(ast, Record):
            return self.visit_record(ast)
        elif isinstance(ast, Sample):
            return self.visit_sample(ast)
        elif isinstance(ast, Slice):
            return self.visit_slice(ast)
        elif isinstance(ast, Negative):
            return self.visit_negative(ast)
        elif isinstance(ast, Scale):
            return self.visit_scale(ast)
        elif isinstance(ast, Add):
            return self.visit_add(ast)
        elif isinstance(ast, Smooth):
            return self.visit_smooth(ast)
        elif isinstance(ast, AlignedWaveform):
            return self.visit_alligned(ast)
        else:
            raise ValueError(f"{ast.__class__} is not a Waveform AST type.")
