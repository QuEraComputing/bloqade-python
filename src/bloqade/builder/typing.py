from bloqade.ir.scalar import Scalar
from decimal import Decimal
from numbers import Real
from beartype.typing import List, Union


ScalarType = Union[Real, Decimal, str, Scalar]
""" 
A type union representing Python-native types (`Real`, `Decimal`, and `str`) and Bloqade's own [`scalar`][bloqade.ir.scalar.Scalar] type
used to represent and manipulate variables within programs.
"""

LiteralType = Union[Real, Decimal]
""" 
A type union representing the `Real` and `Decimal` types used in certain Bloqade methods.
"""

ParamType = Union[LiteralType, List[LiteralType]]
""" 
A type union representing the [`LiteralType`][bloqade.builder.typing.LiteralType] and `List[LiteralType]` types used in certain Bloqade methods.
"""