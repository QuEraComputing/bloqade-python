from bloqade.ir.control.waveform import Waveform
from bloqade.ir.control.field import Field, SpatialModulation
from bloqade.ir.control.pulse import PulseExpr
from bloqade.ir.control.sequence import SequenceExpr
from bloqade.ir.location.base import AtomArrangement, ParallelRegister
from typing import Union, Any

from bloqade.ir.program import Program

AstType = Union[
    Waveform,
    Field,
    SpatialModulation,
    PulseExpr,
    SequenceExpr,
    AtomArrangement,
    ParallelRegister,
]


class ProgramVisitor:
    def visit_waveform(self, ast: Waveform) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for Waveform"
        )

    def visit_field(self, ast: Field) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for Field"
        )

    def visit_spatial_modulation(self, ast: SpatialModulation) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for SpatialModulation"
        )

    def visit_pulse(self, ast: PulseExpr) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for PulseExpr"
        )

    def visit_sequence(self, ast: SequenceExpr) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for SequenceExpr"
        )

    def visit_register(self, ast: AtomArrangement) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for AtomArrangement"
        )

    def visit_parallel_register(self, ast: ParallelRegister) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for MultuplexRegister"
        )

    def visit_program(self, ast: AstType) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for Program"
        )

    def visit(self, ast: AstType) -> Any:
        if isinstance(ast, Waveform):
            return self.visit_waveform(ast)
        elif isinstance(ast, SpatialModulation):
            return self.visit_spatial_modulation(ast)
        elif isinstance(ast, Field):
            return self.visit_field(ast)
        elif isinstance(ast, PulseExpr):
            return self.visit_pulse(ast)
        elif isinstance(ast, SequenceExpr):
            return self.visit_sequence(ast)
        elif isinstance(ast, AtomArrangement):
            return self.visit_register(ast)
        elif isinstance(ast, ParallelRegister):
            return self.visit_parallel_register(ast)
        elif isinstance(ast, Program):
            return self.visit_program(ast)
        else:
            raise NotImplementedError(f"{ast.__class__} is not a bloqade AST type")
