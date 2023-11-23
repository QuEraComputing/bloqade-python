from typing import Any
import bloqade.ir.control.waveform as waveform
from bloqade.ir.visitor import BloqadeIRVisitor
from bloqade.analysis.common.is_constant import IsConstant


class PiecewiseConstantValidator(BloqadeIRVisitor):
    def emit_leaf_error(self, ast: waveform.Waveform):
        expr_msg = str(ast).replace("\n", "\n    ")

        raise ValueError(
            f"failed to compile to piecewise constant, "
            f"found Non-constant segment in waveform:\n    {expr_msg}\n"
        )

    def visit_waveform_Linear(self, ast: waveform.Linear) -> Any:
        if ast.start() != ast.stop():
            self.emit_leaf_error(ast)

    def visit_waveform_Poly(self, ast: waveform.Poly) -> Any:
        if len(ast.coeffs) > 1:
            self.emit_leaf_error(ast)

    def visit_waveform_PythonFn(self, ast: waveform.PythonFn) -> Any:
        self.emit_leaf_error(ast)

    def visit_waveform_Sample(self, ast: waveform.Sample) -> Any:
        if ast.interpolation != waveform.Interpolation.Constant:
            raise ValueError(
                "failed to compile waveform to piecewise linear. "
                f"found non-linear interpolation:\n '{ast.interpolation!s}'"
            )

    def visit_waveform_Smooth(self, ast: waveform.Smooth) -> Any:
        if not IsConstant().scan(ast.waveform):
            self.emit_leaf_error(ast.waveform)

    def scan(self, ast: waveform.Waveform) -> None:
        self.visit(ast)
