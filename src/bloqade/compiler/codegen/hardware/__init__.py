try:
    __import__("pkg_resources").declare_namespace(__name__)
except ImportError:
    __path__ = __import__("pkgutil").extend_path(__path__, __name__)

from .lattice import GenerateLattice
from .lattice_site_coefficients import GenerateLatticeSiteCoefficients
from .piecewise_constant import GeneratePiecewiseConstantChannel, PiecewiseConstant
from .piecewise_linear import GeneratePiecewiseLinearChannel, PiecewiseLinear

__all__ = [
    "GenerateLattice",
    "GenerateLatticeSiteCoefficients",
    "GeneratePiecewiseConstantChannel",
    "GeneratePiecewiseLinearChannel",
    "PiecewiseConstant",
    "PiecewiseLinear",
]
