from dataclasses import dataclass
from typing import Dict
from bloqade.ir.real import Real, Literal, Variable


def merge_dicts(lhs: Dict, rhs: Dict):
    if len(rhs) < len(lhs):
        lhs, rhs = (rhs, lhs)

    rhs = dict(rhs)  # copy data
    for key, value in lhs.items():
        new_value = rhs.get(key, 0) + value
        if new_value == 0:
            del rhs[key]
        else:
            rhs[key] = new_value

    return rhs


class ScalarLang:
    def __add__(self, other):
        if not isinstance(other, ScalarLang):
            raise ValueError("Cannot add non-ScalarLang objects.")

        match (self, other):
            case ((scalar, Scalar(Literal(0.0))) | (Scalar(Literal(0.0)), scalar)):
                return scalar

            case (Scalar(Literal(lhs)), Scalar(Literal(rhs))):
                return Scalar(value=Literal(value=(lhs + rhs)))

            case (scalar, Negative(neg)) | (Negative(neg), scalar) if neg == scalar:
                return Scalar(value=Literal(value=0.0))

            case (Negative(lhs), Negative(rhs)):
                return -(lhs + rhs)

            case (Reduce(head="+") as lhs, Reduce(head="+") as rhs):
                new_args = merge_dicts(lhs.args, rhs.args)
                if len(new_args) == 0:
                    return Scalar(value=Literal(lhs.literal + rhs.literal))
                else:
                    return Reduce(
                        head="+", literal=lhs.literal + rhs.literal, args=new_args
                    )

            case (Reduce(head="+") as reduce, Scalar(Literal(value))) | (
                Scalar(Literal(value)),
                Reduce(head="+") as reduce,
            ):
                return Reduce(
                    head="+", literal=reduce.literal + value, args=reduce.args
                )

            case (Reduce(head="+") as reduce, Negative(scalar)) | (
                Negative(scalar),
                Reduce(head="+") as reduce,
            ):
                new_args = merge_dicts(reduce.args, {scalar: -1})
                if len(new_args) == 0:
                    return Scalar(value=Literal(value=reduce.literal))
                else:
                    return Reduce(head="+", literal=reduce.literal, args=new_args)

            case (Reduce(head="+") as reduce, scalar) | (
                scalar,
                Reduce(head="+") as reduce,
            ):
                new_args = merge_dicts(reduce.args, {scalar: 1})
                if len(new_args) == 0:
                    return Scalar(value=Literal(value=reduce.literal))
                else:
                    return Reduce(head="+", literal=reduce.literal, args=new_args)
            case (Negative(scalar), Scalar(Literal(value))) | (
                Scalar(Literal(value)),
                Negative(scalar),
            ):
                return Reduce(head="+", literal=value, args={scalar: -1})

            case (Negative(neg), scalar) | (scalar, Negative(neg)):
                return Reduce(head="+", literal=0.0, args={neg: -1, scalar: 1})

            case (Scalar(Literal(value)), scalar) | (scalar, Scalar(Literal(value))):
                return Reduce(head="+", literal=value, args={scalar: 1})

            case (lhs, rhs) if (lhs == rhs):
                return Reduce(head="+", literal=0, args={lhs: 2})

            case _:
                return Reduce(head="+", literal=0, args={self: 1, other: 1})

    def __neg__(self):
        match self:
            case Scalar(Literal(0.0)):
                return self

            # pass negative through there variants makes for less canoicalization in addition
            case Scalar(Literal(value)):
                return Scalar(value=Literal(value=-value))

            case Reduce(head="+", literal=literal, args=args):
                return Reduce(
                    head="+", literal=-literal, args={k: -v for k, v in args.items()}
                )

            case Negative(value):
                return value

            case _:
                return Negative(self)

    def __sub__(self, other):
        return self + (-other)


@dataclass(frozen=True)
class Scalar(ScalarLang):
    value: Real

    def julia_adt(self):
        return NotImplemented
        # return ir_types.Scalar(self.value.julia_adt())


@dataclass(frozen=True)
class Negative(ScalarLang):
    value: ScalarLang

    def julia_adt(self):
        return NotImplemented
        # return ir_types.Negative(self.value.julia_adt())


@dataclass(frozen=True)
class Default(ScalarLang):
    var: Variable
    value: float

    def julia_adt(self):
        return NotImplemented
        # return ir_types.Default(self.var.julia_adt(), self.value)


@dataclass(frozen=True)
class Reduce(ScalarLang):
    head: str
    literal: float
    args: Dict[ScalarLang, int]

    def julia_adt(self):
        return NotImplemented
        # return ir_types.Reduce(
        #     self.head,
        #     self.literal,
        #     jl.DictValue(k.julia_adt():v for k,v in self.args.items())
        # )


@dataclass(frozen=True)
class Interval(ScalarLang):
    first: ScalarLang
    last: ScalarLang

    def julia_adt(self):
        return NotImplemented
        # return ir_types.Interval(
        #     self.first.julia_adt(),
        #     self.last.julia_adt()
        # )


@dataclass(frozen=True)
class Slice(ScalarLang):
    duration: ScalarLang
    interval: Interval

    def julia_adt(self):
        return NotImplemented
        # return ir_types.Slice(
        #     self.duration.julia_adt(),
        #     self.interval.julia_adt()
        # )
