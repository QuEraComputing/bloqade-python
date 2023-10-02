from bloqade.ir import var, cast, Variable, Literal, start
from bloqade.ir import to_waveform as waveform
from bloqade.serialize import load, save, loads, dumps

from bloqade.factory import (
    piecewise_linear,
    piecewise_constant,
    linear,
    constant,
    atom_list,
    rydberg_h,
)
import bloqade.ir as _ir
from bloqade.constants import RB_C6

import importlib.metadata

__version__ = importlib.metadata.version("bloqade")


def tree_depth(depth: int = None):
    """Setting globally maximum depth for tree printing

    If `depth=None`, return current depth.
    If `depth` is provided, setting current depth to `depth`

    Args:
        depth (int, optional): the user specified depth. Defaults to None.

    Returns:
        int: current updated depth
    """
    if depth is not None:
        _ir.tree_print.max_tree_depth = depth
    return _ir.tree_print.max_tree_depth


__all__ = [
    "RB_C6",
    "start",
    "var",
    "cast",
    "Variable",
    "Literal",
    "piecewise_linear",
    "piecewise_constant",
    "linear",
    "constant",
    "atom_list",
    "set_print_depth",
    "load",
    "save",
    "loads",
    "dumps",
    "rydberg_h",
    "waveform",
]
