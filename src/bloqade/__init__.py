from bloqade.ir import var, cast, Variable, Literal, start

from bloqade.builder.factory import (
    piecewise_linear,
    piecewise_constant,
    linear,
    constant,
)
import bloqade.ir as _ir


def tree_depth(depth: int = None):
    if depth is not None:
        _ir.tree_print.max_tree_depth = depth
    return _ir.tree_print.max_tree_depth


__all__ = [
    "start",
    "var",
    "cast",
    "Variable",
    "Literal",
    "piecewise_linear",
    "piecewise_constant",
    "linear",
    "constant",
    "set_print_depth",
]
