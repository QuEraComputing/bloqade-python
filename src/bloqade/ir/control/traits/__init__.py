try:
    __import__("pkg_resources").declare_namespace(__name__)
except ImportError:
    __path__ = __import__("pkgutil").extend_path(__path__, __name__)

from .hash import HashTrait
from .append import AppendTrait
from .slice import SliceTrait
from .canonicalize import CanonicalizeTrait

__all__ = [
    "HashTrait",
    "AppendTrait",
    "SliceTrait",
    "CanonicalizeTrait",
]
