from bloqade.ir.scalar import (
    ScalarLang,
    Scalar,
    Negative,
    Default,
    Reduce,
    Slice,
    Interval,
)
import bloqade.ir.real as real


def is_scalar(value):
    return isinstance(value, ScalarLang)


x = Scalar(value=real.Variable("a")) + Scalar(value=real.Literal(1.0))

match x:
    case Scalar(value):
        print(value)
    case Negative(value):
        print(value)
    case [*xs] if all(map(is_scalar, xs)):
        print(x)
    case _:
        print("default")
