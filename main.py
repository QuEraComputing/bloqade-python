from bloqade.ir.scalar import Scalar, Literal, Negative, Default, Reduce, Slice, Interval
import bloqade.ir.real as real

x = [Negative(Literal(i)) for i in range(10)]
print(x[0])

match x:
    case Literal(value):
        print(value)
    case Negative(value):
        print(value)
    case [Negative(Literal(0)), *xs]:
        print(x)
    case _:
        print("default")
