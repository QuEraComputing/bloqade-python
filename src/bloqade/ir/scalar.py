from pydantic.dataclasses import dataclass
from pydantic import validator
from typing import Any, Union, List
from .tree_print import Printer
import re
from decimal import Decimal
import numbers

__all__ = [
    "var",
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

    def __call__(self, **kwargs) -> Decimal:
        match self:
            case Literal(value):
                return value
            case Variable(name):
                if name in kwargs:
                    return Decimal(str(kwargs[name]))
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
        try:
            rhs = cast(other)
        except BaseException:
            return NotImplemented

        return self.add(rhs)

    def __radd__(self, other: "Scalar") -> "Scalar":
        try:
            lhs = cast(other)
        except BaseException:
            return NotImplemented

        return lhs.add(self)

    def __sub__(self, other: "Scalar") -> "Scalar":
        try:
            rhs = cast(other)
        except BaseException:
            return NotImplemented

        return self.sub(rhs)

    def __rsub__(self, other: "Scalar") -> "Scalar":
        try:
            lhs = cast(other)
        except BaseException:
            return NotImplemented

        return lhs.sub(self)

    def __mul__(self, other: "Scalar") -> "Scalar":
        try:
            rhs = cast(other)
        except BaseException:
            return NotImplemented

        return self.mul(rhs)

    def __rmul__(self, other: "Scalar") -> "Scalar":
        try:
            lhs = cast(other)
        except BaseException:
            return NotImplemented

        return lhs.mul(self)

    def __truediv__(self, other: "Scalar") -> "Scalar":
        try:
            rhs = cast(other)
        except BaseException:
            return NotImplemented

        return self.div(rhs)

    def __rtruediv__(self, other: "Scalar") -> "Scalar":
        try:
            lhs = cast(other)
        except BaseException:
            return NotImplemented

        return lhs.div(self)

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

    def __repr__(self) -> str:
        ph = Printer()
        ph.print(self)
        return ph.get_value()

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)

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
            case Negative(Negative(sub_expr)):
                return Scalar.canonicalize(sub_expr)
            case Negative(expr=Literal(value)) if value < 0:
                return Literal(-value)
            case Add(lhs=Literal(lhs), rhs=Literal(rhs)):
                return Literal(lhs + rhs)
            case Add(lhs=Literal(lhs), rhs=Negative(Literal(rhs))):
                return Literal(lhs - rhs)
            case Add(lhs=Negative(Literal(lhs)), rhs=Literal(rhs)):
                return Literal(rhs - lhs)
            case Add(lhs=Literal(0.0), rhs=sub_expr):
                return Scalar.canonicalize(sub_expr)
            case Add(lhs=sub_expr, rhs=Literal(0.0)):
                return Scalar.canonicalize(sub_expr)
            case Add(lhs=sub_expr, rhs=Negative(other_expr)) if sub_expr == other_expr:
                return Literal(0.0)
            case Add(lhs=Negative(sub_expr), rhs=other_expr) if sub_expr == other_expr:
                return Literal(0.0)
            case Mul(lhs=Literal(lhs), rhs=Literal(rhs)):
                return Literal(lhs * rhs)
            case Mul(lhs=Literal(0.0), rhs=_):
                return Literal(0.0)
            case Mul(lhs=_, rhs=Literal(0.0)):
                return Literal(0.0)
            case Mul(lhs=Literal(1.0), rhs=sub_expr):
                return Scalar.canonicalize(sub_expr)
            case Mul(lhs=sub_expr, rhs=Literal(1.0)):
                return Scalar.canonicalize(sub_expr)
            case Div(lhs=Literal(lhs), rhs=Literal(rhs)):
                return Literal(lhs / rhs)
            case Div(lhs=sub_expr, rhs=Literal(1.0)):
                return Scalar.canonicalize(sub_expr)
            case Min(exprs):
                return minmax(Min, exprs)
            case Max(exprs):
                return minmax(Max, exprs)
            case _:
                return expr


def check_variable_name(name: str) -> None:
    regex = "^[A-Za-z_][A-Za-z0-9_]*"
    re_match = re.match(regex, name)
    if re_match.group() != name:
        raise ValueError(f"string '{name}' is not a valid python identifier")


def cast(py) -> Any:
    """cast Real number (or list/tuple of Real numbers)
    to [`Scalar Literal`][bloqade.ir.scalar.Literal].

    Args:
        py (Union[Real,Tuple[Real],List[Real]]): python object to cast

    Returns:
        Union[Literal,Tuple[Literal],List[Literal]]
    """
    ret = trycast(py)
    if ret is None:
        raise TypeError(f"Cannot cast {type(py)} to Scalar Literal")

    return ret


def trycast(py) -> Any:
    match py:
        case int(x) | float(x) | bool(x):
            return Literal(Decimal(str(x)))
        case Decimal():
            return Literal(py)
        case str(x):
            check_variable_name(x)
            return Variable(x)
        case list() as xs:
            return list(map(cast, xs))
        case tuple() as xs:
            return tuple(map(cast, xs))
        case Scalar():
            return py
        case numbers.Real():
            return Literal(Decimal(str(py)))

        case _:
            return


def var(py: Union[str, List[str]]) -> Any:
    """cast string (or list/tuple of strings)
    to [`Variable`][bloqade.ir.scalar.Variable].

    Args:
        py (Union[str, List[str], Tuple[str]]): a string or list/tuple of strings

    Returns:
       Union[Variable, List[Variable], Tuple[Variable]]
    """
    ret = tryvar(py)
    if ret is None:
        raise TypeError(f"Cannot cast {type(py)} to Variable")

    return ret


def tryvar(py) -> Any:
    match py:
        case str(x):
            check_variable_name(x)
            return Variable(x)
        case list() as xs:
            return list(map(var, xs))
        case tuple() as xs:
            return tuple(map(var, xs))
        case Variable():
            return py
        case _:
            return


class Real(Scalar):
    # """Base class for all real expressions."""
    pass


@dataclass(frozen=True)
class Literal(Real):
    value: Decimal
    """Scalar Literal, which stores a decimaal value instance.

    Args:
        value (Decimal): decimal value instance

    """

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self):
        return f"{str(self.value)}"

    def children(self):
        return []

    def print_node(self):
        return f"Literal: {self.value}"

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


@dataclass(frozen=True)
class Variable(Real):
    """Variable, which stores a variable name.

    Args:
        name (str): variable instance.

    """

    name: str

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self):
        return f"var({str(self.name)})"

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

    def __str__(self):
        return f"-({str(self.expr)})"

    def children(self):
        return [self.expr]

    def print_node(self):
        return "-"


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
        ph = Printer()
        ph.print(self)
        return ph.get_value()

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)

    def __str__(self):
        match (self.start, self.stop):
            case (None, None):
                raise ValueError("Interval must have at least one bound")
            case (None, stop):
                return f":{str(stop)}"
            case (start, None):
                return f"{str(start)}:"
            case (start, stop):
                return f"{str(self.start)}:{str(self.stop)}"

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


@dataclass(frozen=True)
class Slice(Scalar):
    expr: Scalar  # duration
    interval: Interval

    def __str__(self):
        return f"{str(self.expr)}[{str(self.interval)}]"

    def children(self):
        return {"Scalar": self.expr, None: self.interval}

    def print_node(self):
        return "Slice"


@dataclass(frozen=True)
class Add(Scalar):
    lhs: Scalar
    rhs: Scalar

    def __str__(self):
        return f"({str(self.lhs)} + {str(self.rhs)})"

    def children(self):
        return [self.lhs, self.rhs]

    def print_node(self):
        return "+"


@dataclass(frozen=True)
class Mul(Scalar):
    lhs: Scalar
    rhs: Scalar

    def __str__(self):
        return f"({str(self.lhs)} * {str(self.rhs)})"

    def children(self):
        return [self.lhs, self.rhs]

    def print_node(self):
        return "*"


@dataclass(frozen=True)
class Div(Scalar):
    lhs: Scalar
    rhs: Scalar

    def __str__(self):
        return f"({str(self.lhs)} / {str(self.rhs)})"

    def children(self):
        return [self.lhs, self.rhs]

    def print_node(self):
        return "/"


@dataclass(frozen=True)
class Min(Scalar):
    exprs: frozenset[Scalar]

    def children(self):
        return list(self.exprs)

    def print_node(self):
        return "min"

    def __str__(self):
        return f"scalar.Min({str(self.exprs)})"


@dataclass(frozen=True)
class Max(Scalar):
    exprs: frozenset[Scalar]

    def children(self):
        return list(self.exprs)

    def print_node(self):
        return "max"

    def __str__(self):
        return f"scalar.Max({str(self.exprs)})"
