from typing import Any
import numpy as np
from pydantic.dataclasses import dataclass
from pydantic import validator
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


@dataclass(frozen=True, repr=False)
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

    # def __call__(self, **kwargs) -> Decimal:
    #     match self:
    #         case Literal(value):
    #             return value
    #         case Variable(name):
    #             if name in kwargs:
    #                 return Decimal(str(kwargs[name]))
    #             else:
    #                 raise Exception(f"Unknown variable: {name}")
    #         case AssignedVariable(name, value):
    #             if name in kwargs:
    #                 raise ValueError(f"Variable {name} already assigned")
    #             else:
    #                 return value
    #         case Negative(expr):
    #             return -expr(**kwargs)
    #         case Add(lhs, rhs):
    #             return lhs(**kwargs) + rhs(**kwargs)
    #         case Mul(lhs, rhs):
    #             return lhs(**kwargs) * rhs(**kwargs)
    #         case Div(lhs, rhs):
    #             return lhs(**kwargs) / rhs(**kwargs)
    #         case Min(exprs):
    #             return min(map(lambda expr: expr(**kwargs), exprs))
    #         case Max(exprs):
    #             return max(map(lambda expr: expr(**kwargs), exprs))
    #         case Slice(expr, Interval(start, stop)):
    #             ret = stop - start
    #             ret <= expr(**kwargs)
    #             return ret
    #         case _:
    #             raise Exception(f"Unknown scalar expression: {self} ({type(self)})")

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

        if isinstance(expr, Negative):
            sub_expr = expr.expr
            if isinstance(sub_expr, Negative):
                return Scalar.canonicalize(sub_expr.expr)
            elif isinstance(sub_expr, Literal) and sub_expr.value < 0:
                return Literal(-sub_expr.value)
        elif isinstance(expr, Add):
            lhs = expr.lhs
            rhs = expr.rhs
            if isinstance(lhs, Literal) and lhs.value == 0:
                return Scalar.canonicalize(rhs)
            elif isinstance(rhs, Literal) and rhs.value == 0:
                return Scalar.canonicalize(lhs)
            elif isinstance(lhs, Literal) and isinstance(rhs, Literal):
                return Literal(lhs.value + rhs.value)
            elif (
                isinstance(lhs, Negative)
                and isinstance(lhs.expr, Literal)
                and isinstance(rhs, Literal)
            ):
                return Literal(rhs.value - lhs.expr.value)
            elif (
                isinstance(rhs, Negative)
                and isinstance(rhs.expr, Literal)
                and isinstance(lhs, Literal)
            ):
                return Literal(lhs.value - rhs.expr.value)
            elif isinstance(lhs, Negative) and lhs.expr == rhs:
                return Literal(0.0)
            elif isinstance(rhs, Negative) and rhs.expr == lhs:
                return Literal(0.0)
        elif isinstance(expr, Mul):
            lhs = expr.lhs
            rhs = expr.rhs
            if isinstance(lhs, Literal) and lhs.value == 1:
                return Scalar.canonicalize(rhs)
            elif isinstance(rhs, Literal) and rhs.value == 1:
                return Scalar.canonicalize(lhs)
            elif isinstance(lhs, Literal) and isinstance(rhs, Literal):
                return Literal(lhs.value * rhs.value)
            elif isinstance(lhs, Literal) and lhs.value == 0:
                return Literal(0.0)
            elif isinstance(rhs, Literal) and rhs.value == 0:
                return Literal(0.0)
        elif isinstance(expr, Div):
            lhs = expr.lhs
            rhs = expr.rhs
            if isinstance(lhs, Literal) and lhs.value == 0:
                return Literal(0.0)
            elif isinstance(rhs, Literal) and rhs.value == 1:
                return Scalar.canonicalize(lhs)
            elif isinstance(lhs, Literal) and isinstance(rhs, Literal):
                return Literal(lhs.value / rhs.value)
        elif isinstance(expr, Min):
            return minmax(Min, expr.exprs)
        elif isinstance(expr, Max):
            return minmax(Max, expr.exprs)

        return expr

        # match expr:
        #     case Negative(Negative(sub_expr)):
        #         return Scalar.canonicalize(sub_expr)
        #     case Negative(expr=Literal(value)) if value < 0:
        #         return Literal(-value)
        #     case Add(lhs=Literal(lhs), rhs=Literal(rhs)):
        #         return Literal(lhs + rhs)
        #     case Add(lhs=Literal(lhs), rhs=Negative(Literal(rhs))):
        #         return Literal(lhs - rhs)
        #     case Add(lhs=Negative(Literal(lhs)), rhs=Literal(rhs)):
        #         return Literal(rhs - lhs)
        #     case Add(lhs=Literal(0.0), rhs=sub_expr):
        #         return Scalar.canonicalize(sub_expr)
        #     case Add(lhs=sub_expr, rhs=Literal(0.0)):
        #         return Scalar.canonicalize(sub_expr)
        #     case Add(lhs=sub_expr, rhs=Negative(other_expr))
        # if (sub_expr == other_expr):
        #         return Literal(0.0)
        #     case Add(lhs=Negative(sub_expr), rhs=other_expr)
        # if (sub_expr == other_expr):
        #         return Literal(0.0)
        #     case Mul(lhs=Literal(lhs), rhs=Literal(rhs)):
        #         return Literal(lhs * rhs)
        #     case Mul(lhs=Literal(0.0), rhs=_):
        #         return Literal(0.0)
        #     case Mul(lhs=_, rhs=Literal(0.0)):
        #         return Literal(0.0)
        #     case Mul(lhs=Literal(1.0), rhs=sub_expr):
        #         return Scalar.canonicalize(sub_expr)
        #     case Mul(lhs=sub_expr, rhs=Literal(1.0)):
        #         return Scalar.canonicalize(sub_expr)
        #     case Div(lhs=Literal(lhs), rhs=Literal(rhs)):
        #         return Literal(lhs / rhs)
        #     case Div(lhs=sub_expr, rhs=Literal(1.0)):
        #         return Scalar.canonicalize(sub_expr)
        #     case Min(exprs):
        #         return minmax(Min, exprs)
        #     case Max(exprs):
        #         return minmax(Max, exprs)
        #     case _:
        #         return expr


def check_variable_name(name: str) -> None:
    regex = "^[A-Za-z_][A-Za-z0-9_]*"
    re_match = re.match(regex, name)
    if re_match.group() != name:
        raise ValueError(f"string '{name}' is not a valid python identifier")


def cast(py) -> "Scalar":
    """
    1. cast Real number (or list/tuple of Real numbers)
    to [`Scalar Literal`][bloqade.ir.scalar.Literal].

    2. cast str (or list/tuple of Real numbers)
    to [`Scalar Variable`][bloqade.ir.scalar.Variable].

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
def trycast(py) -> "Scalar | None":
    # print(type(py))
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
    to [`Variable`][bloqade.ir.scalar.Variable].

    Args:
        py (Union[str, List[str]]): a string or list/tuple of strings

    Returns:
       Union[Variable]
    """
    ret = tryvar(py)
    if ret is None:
        raise TypeError(f"Cannot cast {type(py)} to Variable")

    return ret


def tryvar(py) -> "Variable | None":
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


@dataclass(frozen=True, repr=False)
class Literal(Real):
    value: Decimal
    """Scalar Literal, which stores a decimaal value instance.

    Args:
        value (Decimal): decimal value instance

    """

    def __call__(self, **assignments) -> Decimal:
        return self.value

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


@dataclass(frozen=True, repr=False)
class Variable(Real):
    """Variable, which stores a variable name.

    Args:
        name (str): variable instance.

    """

    name: str

    def __call__(self, **assignments) -> Decimal:
        if self.name not in assignments:
            raise ValueError(f"Variable {self.name} not assigned")

        return Decimal(str(assignments[self.name]))

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
        check_variable_name(v)
        # removing reserved toekn check for now.
        # match v:
        #     case "config_file":
        #         raise ValueError(
        #             f'"{v}" is a reserved token, cannot create variable '
        #               'with that name'
        #         )
        #     case "clock_s":
        #         raise ValueError(
        #             f'"{v}" is a reserved token, cannot create variable '
        #               'with that name'
        #         )
        return v


@dataclass(frozen=True, repr=False)
class AssignedVariable(Scalar):
    name: str
    value: Decimal

    def __call__(self, **assignments) -> Decimal:
        if self.name in assignments:
            raise ValueError(f"Variable {self.name} already assigned")

        return self.value

    def __str__(self):
        return f"{self.name}"

    def children(self):
        return []

    def print_node(self):
        return f"AssignedVariable: {self.name} = {self.value}"

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


@dataclass(frozen=True, repr=False)
class Negative(Scalar):
    expr: Scalar

    def __call__(self, **assignments) -> Decimal:
        return -self.expr(**assignments)

    def __str__(self):
        return f"-({str(self.expr)})"

    def children(self):
        return [self.expr]

    def print_node(self):
        return "Negative"


@dataclass(frozen=True, repr=False)
class Interval:
    start: Scalar | None
    stop: Scalar | None

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


@dataclass(frozen=True, repr=False)
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

    def __str__(self):
        return f"{str(self.expr)}[{str(self.interval)}]"

    def children(self):
        return {"Scalar": self.expr, None: self.interval}

    def print_node(self):
        return "Slice"


@dataclass(frozen=True, repr=False)
class Add(Scalar):
    lhs: Scalar
    rhs: Scalar

    def __call__(self, **assignments) -> Decimal:
        return self.lhs(**assignments) + self.rhs(**assignments)

    def __str__(self):
        return f"({str(self.lhs)} + {str(self.rhs)})"

    def children(self):
        return [self.lhs, self.rhs]

    def print_node(self):
        return "+"


@dataclass(frozen=True, repr=False)
class Mul(Scalar):
    lhs: Scalar
    rhs: Scalar

    def __call__(self, **assignments) -> Decimal:
        return self.lhs(**assignments) * self.rhs(**assignments)

    def __str__(self):
        return f"({str(self.lhs)} * {str(self.rhs)})"

    def children(self):
        return [self.lhs, self.rhs]

    def print_node(self):
        return "*"


@dataclass(frozen=True, repr=False)
class Div(Scalar):
    lhs: Scalar
    rhs: Scalar

    def __call__(self, **assignments) -> Decimal:
        return self.lhs(**assignments) / self.rhs(**assignments)

    def __str__(self):
        return f"({str(self.lhs)} / {str(self.rhs)})"

    def children(self):
        return [self.lhs, self.rhs]

    def print_node(self):
        return "/"


@dataclass(frozen=True, repr=False)
class Min(Scalar):
    exprs: frozenset[Scalar]

    def __call__(self, **assignments) -> Any:
        return min(expr(**assignments) for expr in self.exprs)

    def children(self):
        return list(self.exprs)

    def print_node(self):
        return "min"

    def __str__(self):
        return f"scalar.Min({str(self.exprs)})"


@dataclass(frozen=True, repr=False)
class Max(Scalar):
    exprs: frozenset[Scalar]

    def __call__(self, **assignments) -> Any:
        return max(expr(**assignments) for expr in self.exprs)

    def children(self):
        return list(self.exprs)

    def print_node(self):
        return "max"

    def __str__(self):
        return f"scalar.Max({str(self.exprs)})"
