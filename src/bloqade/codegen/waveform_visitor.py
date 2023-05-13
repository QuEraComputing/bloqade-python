from bloqade.ir.waveform import (
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
)
from typing import Any


class WaveformVisitor:
    def visit_alligned(self, ast: AlignedWaveform) -> Any:
        raise NotADirectoryError(
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
        raise NotADirectoryError(
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

    def visit(self, ast: Waveform):
        match ast:
            case AlignedWaveform():
                return self.visit_alligned(ast)
            case Linear():
                return self.visit_linear(ast)
            case Constant():
                return self.visit_constant(ast)
            case Poly():
                return self.visit_poly(ast)
            case Smooth():
                return self.visit_smooth(ast)
            case Append():
                return self.visit_append(ast)
            case Negative():
                return self.visit_negative(ast)
            case Scale():
                return self.visit_scale(ast)
            case Add():
                return self.visit_add(ast)
            case Record():
                return self.visit_record(ast)
            case _:
                raise ValueError()(f"{ast.__class__} is not a Waveform AST type.")
