from bloqade.ir.waveform import Waveform
from bloqade.ir.field import Field, SpatialModulation
from bloqade.ir.pulse import PulseExpr
from bloqade.ir.sequence import SequenceExpr
from bloqade.lattice.base import Lattice
from typing import Union

AstType = Union[Waveform, Field, SpatialModulation, PulseExpr, SequenceExpr]


class Visitor:
    def visit_waveform(self, ast: Waveform):
        raise NotImplementedError()

    def visit_field(self, ast: Field):
        raise NotImplementedError()

    def visit_spatial_modulation(self, ast: SpatialModulation):
        raise NotImplementedError()

    def visit_pulse(self, ast: PulseExpr):
        raise NotImplementedError()

    def visit_sequence(self, ast: SequenceExpr):
        raise NotImplementedError()

    def visit_lattice(self, ast: Lattice):
        raise NotImplementedError()

    def visit(self, ast: AstType):
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
        elif isinstance(ast, Lattice):
            return self.visit_lattice(ast)
        else:
            raise NotImplementedError(f"{ast} is not a bloqade AST type")
