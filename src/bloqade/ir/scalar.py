from pydantic.dataclasses import dataclass
from pydantic import validator
from typing import Optional
from .tree_print import Printer

__all__ = [
    "cast",
    "Scalar",
    "Interval",
    "Variable",
    "Literal",
]


@dataclass(frozen=True)
class Scalar:
    """Base class for all scalar expressions.

    ```bnf
    <scalar> ::= <literal>
    | <variable>
    | <default>
    | <negative>
    | <add>
    | <mul>
    | <min>
    | <max>
    | <slice>
    | <inverval>

    <mul> ::= <scalar> '*' <scalar>
    <add> ::= <scalar> '+' <scalar>
    <min> ::= 'min' <scalar>+
    <max> ::= 'max' <scalar>+
    <slice> ::= <scalar expr> '[' <interval> ']'
    <interval> ::= <scalar expr> '..' <scalar expr>
    <real> ::= <literal> | <var>
    ```
    """

    def __call__(self, **kwargs):
        match self:
            case Literal(value):
                return value
            case Variable(name):
                if name in kwargs:
                    return kwargs[name]
                else:
                    raise Exception(f"Unknown variable: {name}")
            case Negative(expr):
                return -expr(**kwargs)
            case Add(lhs, rhs):
                return lhs(**kwargs) + rhs(**kwargs)
            case Mul(lhs, rhs):
                return lhs(**kwargs) * rhs(**kwargs)
            case Div(lhs, rhs):
                return lhs(**kwargs) / rhs(**kwargs)
            case Min(exprs):
                return min(map(lambda expr: expr(**kwargs), exprs))
            case Max(exprs):
                return max(map(lambda expr: expr(**kwargs), exprs))
            case Slice(expr, Interval(start, stop)):
                ret = stop - start
                ret <= expr(**kwargs)
                return ret
            case _:
                raise Exception(f"Unknown scalar expression: {self} ({type(self)})")

    def __add__(self, other: "Scalar") -> "Scalar":
        expr = Add(lhs=self, rhs=other)
        return Scalar.canonicalize(expr)

    def __sub__(self, other: "Scalar") -> "Scalar":
        expr = Add(lhs=self, rhs=-cast(other))
        return Scalar.canonicalize(expr)

    def __mul__(self, other: "Scalar") -> "Scalar":
        expr = Mul(lhs=self, rhs=other)
        return Scalar.canonicalize(expr)

    def __neg__(self) -> "Scalar":
        return Scalar.canonicalize(Negative(self))

    def add(self, other) -> "Scalar":
        expr = Add(lhs=self, rhs=cast(other))
        return Scalar.canonicalize(expr)

    def sub(self, other) -> "Scalar":
        expr = Add(lhs=self, rhs=-cast(other))
        return Scalar.canonicalize(expr)

    def mul(self, other) -> "Scalar":
        expr = Mul(lhs=self, rhs=cast(other))
        return Scalar.canonicalize(expr)

    def div(self, other) -> "Scalar":
        expr = Div(lhs=self, rhs=cast(other))
        return Scalar.canonicalize(expr)

    def min(self, other) -> "Scalar":
        expr = Min(exprs=frozenset({self, cast(other)}))
        return Scalar.canonicalize(expr)

    def max(self, other) -> "Scalar":
        expr = Max(exprs=frozenset({self, cast(other)}))
        return Scalar.canonicalize(expr)

    @staticmethod
    def canonicalize(expr: "Scalar") -> "Scalar":
        def minmax(op, exprs):
            new_exprs = set()
            for expr in exprs:
                match expr:
                    case op(exprs):
                        exprs = map(Scalar.canonicalize, exprs)
                        new_exprs.update(exprs)
                    case _:
                        expr = Scalar.canonicalize(expr)
                        new_exprs.add(expr)

            if len(new_exprs) > 1:
                return op(exprs=frozenset(new_exprs))
            else:
                (new_expr,) = new_exprs
                return new_expr

        match expr:
            case Negative(Negative(expr)):
                return Scalar.canonicalize(expr)
            case Negative(Literal(value)) if value < 0:
                return Literal(-value)
            case Add(Literal(lhs), Literal(rhs)):
                return Literal(lhs + rhs)
            case Add(Literal(0.0), expr):
                return Scalar.canonicalize(expr)
            case Add(expr, Literal(0.0)):
                return Scalar.canonicalize(expr)
            case Add(expr, Negative(other_expr)) if expr == other_expr:
                return Literal(0.0)
            case Mul(Literal(lhs), Literal(rhs)):
                return Literal(lhs * rhs)
            case Mul(Literal(0.0), _):
                return Literal(0.0)
            case Mul(_, Literal(0.0)):
                return Literal(0.0)
            case Mul(Literal(1.0), expr):
                return Scalar.canonicalize(expr)
            case Mul(expr, Literal(1.0)):
                return Scalar.canonicalize(expr)
            case Min(exprs):
                return minmax(Min, exprs)
            case Max(exprs):
                return minmax(Max, exprs)
            case _:
                return expr


def cast(py) -> Scalar:
    ret = trycast(py)
    if ret is None:
        raise TypeError(f"Cannot cast {py} to Scalar")
    else:
        return ret


def trycast(py) -> Optional[Scalar]:
    match py:
        case int(x) | float(x) | bool(x):
            return Literal(x)
        case str(x):
            return Variable(x)
        case list() as xs:
            return list(map(cast, xs))
        case Scalar():
            return py
        case _:
            return


class Real(Scalar):
    """Base class for all real expressions."""

    pass


@dataclass(frozen=True)
class Literal(Real):
    value: float

    def __repr__(self) -> str:
        return f"{self.value!r}"

    def children(self):
        return []

    def print_node(self):
        return f"Literal: {self.value}"

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


@dataclass(frozen=True)
class Variable(Real):
    name: str

    def __repr__(self) -> str:
        return f"{self.name!r}"

    def children(self):
        return []

    def print_node(self):
        return f"Variable: {self.name}"

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)

    @validator("name")
    def name_validator(cls, v):
        match v:
            case "config_file":
                raise ValueError(
                    f'"{v}" is a reserved token, cannot create variable with that name'
                )
            case "clock_s":
                raise ValueError(
                    f'"{v}" is a reserved token, cannot create variable with that name'
                )

        return v


@dataclass(frozen=True)
class Negative(Scalar):
    expr: Scalar

    def __repr__(self) -> str:
        return f"-({self.expr!r})"

    def children(self):
        return [self.expr]

    def print_node(self):
        return "-"

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


@dataclass(frozen=True)
class Interval:
    start: Scalar | None
    stop: Scalar | None

    @staticmethod
    def from_slice(s: slice) -> "Interval":
        match s:
            case slice(start=None, stop=None, step=None):
                raise ValueError("Slice must have at least one argument")
            case slice(start=None, stop=None, step=_):
                raise ValueError("Slice step must be None")
            case slice(start=None, stop=stop, step=None):
                return Interval(None, cast(stop))
            case slice(start=None, stop=stop, step=_):
                raise ValueError("Slice step must be None")
            case slice(start=start, stop=None, step=None):
                return Interval(cast(start), None)
            case slice(start=start, stop=None, step=_):
                raise ValueError("Slice step must be None")
            case slice(start=start, stop=stop, step=None):
                return Interval(cast(start), cast(stop))
            case slice(start=start, stop=stop, step=_):
                raise ValueError("Slice step must be None")

    def __repr__(self) -> str:
        match (self.start, self.stop):
            case (None, None):
                raise ValueError("Interval must have at least one bound")
            case (None, stop):
                return f":{stop!r}"
            case (start, None):
                return f"{start!r}:"
            case (start, stop):
                return f"{self.start!r}:{self.stop!r}"

    def print_node(self):
        return "Interval"

    def children(self):
        match (self.start, self.stop):
            case (None, None):
                raise ValueError("Interval must have at least one bound")
            case (None, stop):
                return {"stop": stop}
            case (start, None):
                return {"start": start}
            case (start, stop):
                return {"start": start, "stop": stop}

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


@dataclass(frozen=True)
class Slice(Scalar):
    expr: Scalar  # duration
    interval: Interval

    def __repr__(self) -> str:
        return f"{self.expr!r}[{self.interval!r}]"

    def children(self):
        return {"Scalar": self.expr, None: self.interval}

    def print_node(self):
        return "Slice"

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


@dataclass(frozen=True)
class Add(Scalar):
    lhs: Scalar
    rhs: Scalar

    def __repr__(self) -> str:
        return f"({self.lhs!r} + {self.rhs!r})"

    def children(self):
        return [self.lhs, self.rhs]

    def print_node(self):
        return "+"

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


@dataclass(frozen=True)
class Mul(Scalar):
    lhs: Scalar
    rhs: Scalar

    def __repr__(self) -> str:
        return f"({self.lhs!r} * {self.rhs!r})"

    def children(self):
        return [self.lhs, self.rhs]

    def print_node(self):
        return "*"

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


@dataclass(frozen=True)
class Div(Scalar):
    lhs: Scalar
    rhs: Scalar

    def __repr__(self) -> str:
        return f"({self.lhs!r} / {self.rhs!r})"

    def children(self):
        return [self.lhs, self.rhs]

    def print_node(self):
        return "/"

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


@dataclass(frozen=True)
class Min(Scalar):
    exprs: frozenset[Scalar]

    def children(self):
        return list(self.exprs)

    def print_node(self):
        return "min"

    def __repr__(self) -> str:
        return f"scalar.Min({self.exprs!r})"

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


@dataclass(frozen=True)
class Max(Scalar):
    exprs: frozenset[Scalar]

    def children(self):
        return list(self.exprs)

    def print_node(self):
        return "max"

    def __repr__(self) -> str:
        return f"scalar.Max({self.exprs!r})"

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)
