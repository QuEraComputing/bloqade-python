from functools import cached_property
from bloqade.ir.scalar import cast


class AppendTrait:
    @property
    def _sub_exprs(self):
        raise NotImplementedError("sub_exprs property is not implemented")

    @cached_property
    def duration(self):
        duration = cast(0)
        for p in self._sub_exprs:
            duration = duration + p.duration

        return duration
