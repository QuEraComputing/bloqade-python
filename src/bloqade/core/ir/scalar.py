from typing import Any, Optional
import numpy as np
from pydantic.dataclasses import dataclass
from pydantic import ValidationError, validator
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

    def __getitem__(self, s: slice) -> "Scalar":
        return Scalar.canonicalize(Slice(self, Interval.from_slice(s)))

    def __add__(self, other: "Scalar") -> "Scalar":
        return self.add(other)

    def __sub__(self, other: "Scalar") -> "Scalar":
        return self.sub(other)

    def __mul__(self, other: "Scalar") -> "Scalar":
        return self.mul(other)

    def __truediv__(self, other: "Scalar") -> "Scalar":
        return self.div(other)

    def __radd__(self, other: "Scalar") -> "Scalar":
        try:
            lhs = cast(other)
        except TypeError:
            return NotImplemented

        if not isinstance(lhs, Scalar):
            return NotImplemented

        return lhs.add(self)

    def __rsub__(self, other: "Scalar") -> "Scalar":
        try:
            lhs = cast(other)
        except TypeError:
            return NotImplemented

        if not isinstance(lhs, Scalar):
            return NotImplemented

        return lhs.sub(self)

    def __rmul__(self, other: "Scalar") -> "Scalar":
        try:
            lhs = cast(other)
        except TypeError:
            return NotImplemented

        if not isinstance(lhs, Scalar):
            return NotImplemented

        return lhs.mul(self)

    def __rtruediv__(self, other: "Scalar") -> "Scalar":
        try:
            lhs = cast(other)
        except TypeError:
            return NotImplemented

        if not isinstance(lhs, Scalar):
            return NotImplemented

        return lhs.div(self)

    def __neg__(self) -> "Scalar":
        return Scalar.canonicalize(Negative(self))

    def add(self, other) -> "Scalar":
        try:
            rhs = cast(other)
        except TypeError:
            return NotImplemented

        if not isinstance(rhs, Scalar):
            return NotImplemented

        expr = Add(lhs=self, rhs=rhs)
        return Scalar.canonicalize(expr)

    def sub(self, other) -> "Scalar":
        try:
            rhs = cast(other)
        except TypeError:
            return NotImplemented

        if not isinstance(rhs, Scalar):
            return NotImplemented

        expr = Add(lhs=self, rhs=-rhs)
        return Scalar.canonicalize(expr)

    def mul(self, other) -> "Scalar":
        try:
            rhs = cast(other)
        except TypeError:
            return NotImplemented

        if not isinstance(rhs, Scalar):
            return NotImplemented

        expr = Mul(lhs=self, rhs=rhs)
        return Scalar.canonicalize(expr)

    def div(self, other) -> "Scalar":
        try:
            rhs = cast(other)
        except TypeError:
            return NotImplemented

        if not isinstance(rhs, Scalar):
            return NotImplemented

        expr = Div(lhs=self, rhs=rhs)
        return Scalar.canonicalize(expr)

    def min(self, other) -> "Scalar":
        try:
            other_expr = cast(other)
        except TypeError:
            return NotImplemented

        expr = Min(exprs=frozenset({self, other_expr}))
        return Scalar.canonicalize(expr)

    def max(self, other) -> "Scalar":
        try:
            other_expr = cast(other)
        except TypeError:
            return NotImplemented

        expr = Max(exprs=frozenset({self, other_expr}))
        return Scalar.canonicalize(expr)

    def __str__(self) -> str:
        ph = Printer()
        ph.print(self)
        return ph.get_value()

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)

    @staticmethod
    def canonicalize(expr: "Scalar") -> "Scalar":
        from bloqade.core.compiler.rewrite.common.canonicalize import Canonicalizer

        return Canonicalizer().visit(expr)


def check_variable_name(name: str) -> None:
    regex = "^[A-Za-z_][A-Za-z0-9_]*"
    re_match = re.match(regex, name)
    if re_match.group() != name:
        raise ValidationError(f"string '{name}' is not a valid python identifier")


def cast(py) -> "Scalar":
    """
    1. cast Real number (or list/tuple of Real numbers)
    to [`Scalar Literal`][bloqade.core.ir.scalar.Literal].

    2. cast str (or list/tuple of Real numbers)
    to [`Scalar Variable`][bloqade.core.ir.scalar.Variable].

    Args:
        py (Union[str,Real,Tuple[Real],List[Real]]): python object to cast

    Returns:
        Scalar
    """
    ret = trycast(py)
    if ret is None:
        raise TypeError(f"Cannot cast {type(py)} to Scalar Literal")

    return ret


# TODO: RL: remove support on List and Tuple just use map?
#       this is making type inference much harder to parse
#       in human brain
# [KHW] it need to be there. For recursive replace for nested
#       list/tuple
def trycast(py) -> Optional[Scalar]:
    if isinstance(py, (int, bool, numbers.Real)):
        return Literal(Decimal(str(py)))
    elif isinstance(py, Decimal):
        return Literal(py)
    elif isinstance(py, str):
        return Variable(py)
    elif isinstance(py, Scalar):
        return py
    elif isinstance(py, (list, tuple)):
        return type(py)(map(cast, py))
    elif isinstance(py, np.ndarray):
        return np.array(list(map(cast, py)))
    else:
        return


def var(py: str) -> "Variable":
    """cast string (or list/tuple of strings)
    to [`Variable`][bloqade.core.ir.scalar.Variable].

    Args:
        py (Union[str, List[str]]): a string or list/tuple of strings

    Returns:
       Union[Variable]
    """
    ret = tryvar(py)
    if ret is None:
        raise TypeError(f"Cannot cast {type(py)} to Variable")

    return ret


def tryvar(py) -> Optional["Variable"]:
    if isinstance(py, str):
        return Variable(py)
    if isinstance(py, Variable):
        return py
    elif isinstance(py, (list, tuple)):
        return type(py)(map(var, py))
    else:
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

    def __call__(self, **assignments) -> Decimal:
        return self.value

    def __str__(self) -> str:
        return str(self.value)

    def children(self):
        return []

    def print_node(self):
        return f"Literal: {self.value}"

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


@dataclass(frozen=True)
class Variable(Real):
    """Variable, which stores a variable name.

    Attributes:
        name (str): variable instance.

    """

    name: str

    def __call__(self, **assignments) -> Decimal:
        if self.name not in assignments:
            raise ValueError(f"Variable {self.name} not assigned")

        return Decimal(str(assignments[self.name]))

    def __str__(self) -> str:
        return self.name

    def children(self):
        return []

    def print_node(self):
        return f"Variable: {self.name}"

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)

    @validator("name", allow_reuse=True)
    def validate_name(cls, name):
        check_variable_name(name)
        if name in ["__batch_params"]:
            raise ValidationError(
                "Cannot use reserved name `__batch_params` for variable name"
            )

        return name


@dataclass(frozen=True)
class AssignedVariable(Scalar):
    name: str
    value: Decimal

    def __call__(self, **assignments) -> Decimal:
        if self.name in assignments:
            raise ValueError(f"Variable {self.name} already assigned")

        return self.value

    def __str__(self) -> str:
        return f"{self.name}"

    def children(self):
        return []

    def print_node(self):
        return f"AssignedVariable: {self.name} = {self.value!s}"

    @validator("name", allow_reuse=True)
    def validate_name(cls, name):
        check_variable_name(name)
        if name in ["__batch_params"]:
            raise ValidationError(
                "Cannot use reserved name `__batch_params` for variable name"
            )

        return name


@dataclass(frozen=True)
class Negative(Scalar):
    expr: Scalar

    def __call__(self, **assignments) -> Decimal:
        return -self.expr(**assignments)

    def __str__(self) -> str:
        return f"-({self.expr!s})"

    def children(self):
        return [self.expr]

    def print_node(self):
        return "Negative"


@dataclass(frozen=True)
class Interval:
    start: Optional[Scalar]
    stop: Optional[Scalar]

    @staticmethod
    def from_slice(s: slice) -> "Interval":
        start, stop, step = s.start, s.stop, s.step

        if start is None and stop is None and step is None:
            raise ValueError("Slice must have at least one argument")
        elif step is not None:
            raise ValueError("Slice step must be None")

        else:
            if start is None:
                start = None
            else:
                start = cast(start)
                if not isinstance(start, Scalar):
                    raise ValueError("Slice start must be Scalar")

            if stop is None:
                stop = None
            else:
                stop = cast(stop)
                if not isinstance(stop, Scalar):
                    raise ValueError("Slice stop must be Scalar")

            return Interval(start, stop)

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)

    def __str__(self):
        if self.start is None:
            if self.stop is None:
                raise ValueError("Interval must have at least one bound")
            else:
                return f":{str(self.stop)}"
        else:
            if self.stop is None:
                return f"{str(self.start)}:"
            else:
                return f"{str(self.start)}:{str(self.stop)}"

    def print_node(self):
        return "Interval"

    def children(self):
        if self.start is None:
            if self.stop is None:
                raise ValueError("Interval must have at least one bound")
            else:
                return {"stop": self.stop}
        else:
            if self.stop is None:
                return {"start": self.start}
            else:
                return {"start": self.start, "stop": self.stop}


@dataclass(frozen=True)
class Slice(Scalar):
    expr: Scalar  # duration
    interval: Interval

    def __call__(self, **assignments) -> Decimal:
        dur = self.expr(**assignments)
        start = (
            self.interval.start(**assignments)
            if self.interval.start is not None
            else Decimal("0")
        )
        stop = (
            self.interval.stop(**assignments) if self.interval.stop is not None else dur
        )

        if start < 0:
            raise ValueError(
                f"Slice start must be non-negative, got {start} from expr:\n"
                f"{repr(self.interval.start)}\n"
                f"with assignments: {assignments}"
            )

        if stop > dur:
            raise ValueError(
                "Slice stop must be smaller or equal to than duration "
                f"{dur}, got {stop} from expr:\b"
                f"{repr(self.interval.stop)}\n"
                f"with assignments: {assignments}"
            )

        ret = stop - start

        if ret < 0:
            raise ValueError(
                f"start is larger than stop, get start = {start} and stop = {stop}\n"
                "from start expr:\n"
                f"{repr(self.interval.start)}\n"
                "and stop expr:\n"
                f"{repr(self.interval.stop)}\n"
                f"with assignments: {assignments}"
            )

        return ret

    def __str__(self) -> str:
        return f"({self.expr!s})[{self.interval!s}]"

    def children(self):
        return {"Scalar": self.expr, None: self.interval}

    def print_node(self):
        return "Slice"


@dataclass(frozen=True)
class Add(Scalar):
    lhs: Scalar
    rhs: Scalar

    def __call__(self, **assignments) -> Decimal:
        return self.lhs(**assignments) + self.rhs(**assignments)

    def __str__(self) -> str:
        return f"({self.lhs!s} + {self.rhs!s})"

    def children(self):
        return [self.lhs, self.rhs]

    def print_node(self):
        return "+"


@dataclass(frozen=True)
class Mul(Scalar):
    lhs: Scalar
    rhs: Scalar

    def __call__(self, **assignments) -> Decimal:
        return self.lhs(**assignments) * self.rhs(**assignments)

    def __str__(self) -> str:
        return f"({self.lhs!s} * {self.rhs!s})"

    def children(self):
        return [self.lhs, self.rhs]

    def print_node(self):
        return "*"


@dataclass(frozen=True)
class Div(Scalar):
    lhs: Scalar
    rhs: Scalar

    def __call__(self, **assignments) -> Decimal:
        return self.lhs(**assignments) / self.rhs(**assignments)

    def __str__(self) -> str:
        return f"({self.lhs!s} / {self.rhs!s})"

    def children(self):
        return [self.lhs, self.rhs]

    def print_node(self):
        return "/"


@dataclass(frozen=True)
class Min(Scalar):
    exprs: frozenset[Scalar]

    def __call__(self, **assignments) -> Any:
        return min(expr(**assignments) for expr in self.exprs)

    def __str__(self) -> str:
        return f"min({', '.join(map(str, self.exprs))})"

    def children(self):
        return list(self.exprs)

    def print_node(self):
        return "min"


@dataclass(frozen=True)
class Max(Scalar):
    exprs: frozenset[Scalar]

    def __call__(self, **assignments) -> Any:
        return max(expr(**assignments) for expr in self.exprs)

    def children(self):
        return list(self.exprs)

    def print_node(self):
        return "max"

    def __str__(self) -> str:
        return f"max({', '.join(map(str, self.exprs))})"
