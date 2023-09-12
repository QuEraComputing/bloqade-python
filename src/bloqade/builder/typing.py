from bloqade.ir.scalar import Scalar
from decimal import Decimal
from numbers import Real
from beartype import List, Union


ScalarType = Union[Real, Decimal, str, Scalar]
LiteralType = Union[Real, Decimal]
ParamType = Union[LiteralType, List[LiteralType]]
