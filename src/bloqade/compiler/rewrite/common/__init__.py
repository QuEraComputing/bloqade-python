try:
    __import__("pkg_resources").declare_namespace(__name__)
except ImportError:
    __path__ = __import__("pkgutil").extend_path(__path__, __name__)

from .add_padding import AddPadding
from .assign_to_literal import AssignToLiteral
from .assign_variables import AssignBloqadeIR
from .canonicalize import Canonicalizer
from .flatten import FlattenCircuit

__all__ = [
    "AddPadding",
    "AssignToLiteral",
    "AssignBloqadeIR",
    "Canonicalizer",
    "FlattenCircuit",
]
