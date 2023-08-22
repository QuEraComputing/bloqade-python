from bloqade.ir.scalar import (
    Scalar,
    Literal,
    Variable,
    DefaultVariable,
    Negative,
    Add,
    Mul,
    Div,
    Max,
    Min,
    Slice,
    Interval,
)
from typing import Any


class ScalarVisitor:
    def visit_literal(self, ast: Literal) -> Any:
        raise NotImplementedError(
            f"visit_literal not implemented for {self.__class__.__name__}"
        )

    def visit_variable(self, ast: Variable) -> Any:
        raise NotImplementedError(
            f"visit_variable not implemented for {self.__class__.__name__}"
        )

    def visit_default_variable(self, ast: DefaultVariable) -> Any:
        raise NotImplementedError(
            f"visit_default_variable not implemented for {self.__class__.__name__}"
        )

    def visit_negative(self, ast: Negative) -> Any:
        raise NotImplementedError(
            f"visit_negative not implemented for {self.__class__.__name__}"
        )

    def visit_add(self, ast: Add) -> Any:
        raise NotImplementedError(
            f"visit_add not implemented for {self.__class__.__name__}"
        )

    def visit_mul(self, ast: Mul) -> Any:
        raise NotImplementedError(
            f"visit_mul not implemented for {self.__class__.__name__}"
        )

    def visit_div(self, ast: Div) -> Any:
        raise NotImplementedError(
            f"visit_div not implemented for {self.__class__.__name__}"
        )

    def visit_max(self, ast: Max) -> Any:
        raise NotImplementedError(
            f"visit_max not implemented for {self.__class__.__name__}"
        )

    def visit_min(self, ast: Min) -> Any:
        raise NotImplementedError(
            f"visit_min not implemented for {self.__class__.__name__}"
        )

    def visit_slice(self, ast: Slice) -> Any:
        raise NotImplementedError(
            f"visit_slice not implemented for {self.__class__.__name__}"
        )

    def visit_interval(self, ast: Interval) -> Any:
        raise NotImplementedError(
            f"visit_interval not implemented for {self.__class__.__name__}"
        )

    def visit(self, ast: Scalar) -> Any:
        if isinstance(ast, Literal):
            return self.visit_literal(ast)
        elif isinstance(ast, Variable):
            return self.visit_variable(ast)
        elif isinstance(ast, DefaultVariable):
            return self.visit_default_variable(ast)
        elif isinstance(ast, Negative):
            return self.visit_negative(ast)
        elif isinstance(ast, Add):
            return self.visit_add(ast)
        elif isinstance(ast, Mul):
            return self.visit_mul(ast)
        elif isinstance(ast, Div):
            return self.visit_div(ast)
        elif isinstance(ast, Max):
            return self.visit_max(ast)
        elif isinstance(ast, Min):
            return self.visit_min(ast)
        elif isinstance(ast, Slice):
            return self.visit_slice(ast)
        elif isinstance(ast, Interval):
            return self.visit_interval(ast)
        else:
            raise NotImplementedError(f"unknown ast type {ast.__class__.__name__}")
