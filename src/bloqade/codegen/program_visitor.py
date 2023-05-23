from bloqade.ir.waveform import Waveform
from bloqade.ir.field import Field, SpatialModulation
from bloqade.ir.pulse import PulseExpr
from bloqade.ir.sequence import SequenceExpr
from bloqade.ir.location.base import AtomArrangement, MultuplexRegister
from typing import Union, Any

AstType = Union[
    Waveform,
    Field,
    SpatialModulation,
    PulseExpr,
    SequenceExpr,
    AtomArrangement,
    MultuplexRegister,
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

    def visit_multiplex_register(self, ast: MultuplexRegister) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for MultuplexRegister"
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
        elif isinstance(ast, MultuplexRegister):
            return self.visit_multiplex_register(ast)
        else:
            raise NotImplementedError(f"{ast.__class__} is not a bloqade AST type")
