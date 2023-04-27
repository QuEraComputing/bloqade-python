from pydantic.dataclasses import dataclass
from ..julia import IRTypes, ToJulia
from juliacall import AnyValue  # type: ignore


@dataclass(frozen=True)
class Scalar(ToJulia):
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
    
    def __call__(self,**variable_reference):
        return NotImplemented

    def __add__(self, other: "Scalar") -> "Scalar":
        expr = Add(lhs=self, rhs=other)
        return Scalar.canonicalize(expr)

    def __sub__(self, other: "Scalar") -> "Scalar":
        expr = Add(lhs=self, rhs=-other)
        return Scalar.canonicalize(expr)

    def __mul__(self, other: "Scalar") -> "Scalar":
        expr = Mul(lhs=self, rhs=other)
        return Scalar.canonicalize(expr)

    def __neg__(self) -> "Scalar":
        return Scalar.canonicalize(Negative(self))

    def min(self, other: "Scalar") -> "Scalar":
        expr = Min(exprs=frozenset({self, other}))
        return Scalar.canonicalize(expr)

    def max(self, other: "Scalar") -> "Scalar":
        expr = Max(exprs=frozenset({self, other}))
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
                new_expr, = new_exprs
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


class Real(Scalar):
    """Base class for all real expressions."""

    pass


@dataclass(frozen=True)
class Literal(Real):
    value: float

    def __repr__(self) -> str:
        return f"{self.value}"

    def julia(self) -> AnyValue:
        return IRTypes.Scalar(IRTypes.Literal(self.value))


@dataclass(frozen=True)
class Variable(Real):
    name: str

    def __repr__(self) -> str:
        return f"{self.name}"

    def julia(self) -> AnyValue:
        return IRTypes.Scalar(IRTypes.Variable(IRTypes.Symbol(self.name)))


@dataclass(frozen=True)
class Negative(Scalar):
    expr: Scalar

    def __repr__(self) -> str:
        return f"-{self.expr}"

    def julia(self) -> AnyValue:
        return IRTypes.Negative(self.expr.julia())


@dataclass(frozen=True)
class Interval(Scalar):
    start: Scalar
    end: Scalar

    def __repr__(self) -> str:
        return f"{self.start}..{self.end}"

    def julia(self):
        return IRTypes.Interval(self.start.julia(), self.end.julia())


@dataclass(frozen=True)
class Slice(Scalar):
    expr: Scalar
    interval: Interval

    def __repr__(self) -> str:
        return f"{self.expr}[{self.interval}]"


@dataclass(frozen=True)
class Add(Scalar):
    lhs: Scalar
    rhs: Scalar

    def __repr__(self) -> str:
        return f"{self.lhs} + {self.rhs}"

    def julia(self) -> AnyValue:
        return IRTypes.Add(self.lhs.julia(), self.rhs.julia())


@dataclass(frozen=True)
class Mul(Scalar):
    lhs: Scalar
    rhs: Scalar

    def __repr__(self) -> str:
        return f"{self.lhs} * {self.rhs}"


@dataclass(frozen=True)
class Min(Scalar):
    exprs: frozenset[Scalar]

    def __repr__(self) -> str:
        return f"min({', '.join(map(str, self.exprs))})"


@dataclass(frozen=True)
class Max(Scalar):
    exprs: frozenset[Scalar]

    def __repr__(self) -> str:
        return f"max({', '.join(map(str, self.exprs))})"
