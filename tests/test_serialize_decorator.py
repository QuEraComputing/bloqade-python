from bloqade.serialize import Serializer, dumps, loads
from beartype.typing import Union, Dict, Any
from beartype import beartype
from decimal import Decimal
from numbers import Real


LiteralType = Union[Decimal, Real]


@Serializer.register
class A:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, A):
            return self.x == __value.x and self.y == __value.y

        return False


@Serializer.register
class B:
    def __init__(self, x: float, y):
        self._x = x
        self._y = y

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, B):
            return self._x == __value._x and self._y == __value._y


@B.set_serializer
def _serialize(obj: B):
    return {"x": obj._x, "y": obj._y}


@Serializer.register
class C:
    @beartype
    def __init__(self, x: LiteralType):
        self._x = Decimal(str(x))
        self._y = 2 * x

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, C):
            return self._x == __value._x

        return False


@C.set_serializer
def _serializer(obj: C) -> Dict[str, Any]:
    return {"x": obj._x}


@C.set_deserializer
def _deserializer(d: Dict[str, Any]) -> C:
    d = {"x": Decimal(d["x"])}
    return C(**d)


def test():
    assert f'{{"{A.__module__}.A": {{"x": 1, "y": 2}}}}' == dumps(A(1, 2)), repr(
        A(1, 2)
    )
    assert f'{{"{B.__module__}.B": {{"x": 1, "y": 2}}}}' == dumps(B(1, 2)), repr(
        dumps(B(1, 2))
    )
    assert f'{{"{C.__module__}.C": {{"x": 1.23091023939020342342039402304}}}}' == dumps(
        C(Decimal("1.23091023939020342342039402304"))
    )

    assert B(C(1), A(1, 2)) == loads(dumps(B(C(1), A(1, 2))))
    assert A(1, B(1, 2)) == loads(dumps(A(1, B(1, 2))))
    assert A(A(A(A(1, 2), 3), 4), C(4)) == loads(dumps(A(A(A(A(1, 2), 3), 4), C(4))))

    a = A("a", "b")
    a = A(a, "c")
    a = A(1, a)
    a = A(B(a, C(1)), B("A", a))
    a = A(B(1, 2), A(a, C(2)))

    assert a == loads(dumps(a))


test()
