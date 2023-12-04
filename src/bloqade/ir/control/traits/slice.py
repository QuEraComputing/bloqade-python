from functools import cached_property
from bloqade.ir.scalar import Scalar, cast


class SliceTraits:
    @property
    def sub_expr(self):
        raise NotImplementedError("sub_expr property is not implemented")

    @cached_property
    def start(self) -> Scalar:
        if self.interval.start is None:
            return cast(0)
        else:
            return self.interval.start

    @cached_property
    def stop(self) -> Scalar:
        if self.interval.stop is None:
            return self.sub_expr.duration
        else:
            return self.interval.stop

    @cached_property
    def duration(self) -> Scalar:
        return self.sub_expr.duration[self.start : self.stop]
