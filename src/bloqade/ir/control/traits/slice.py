from functools import cached_property
from bloqade.ir.scalar import Scalar, cast


class SliceTrait:
    @property
    def _sub_expr(self):
        raise NotImplementedError("sub_expr property is not implemented")

    @cached_property
    def start(self) -> Scalar:
        """Start time of the sliced object

        Returns:
            Scalar: The starting time of the sliced object as a
            Scalar Expression
        """
        if self.interval.start is None:
            return cast(0)
        else:
            return self.interval.start

    @cached_property
    def stop(self) -> Scalar:
        """Stop time of the sliced object

        Returns:
            Scalar: The stopping time of the sliced object as a
            Scalar Expression
        """
        if self.interval.stop is None:
            return self._sub_expr.duration
        else:
            return self.interval.stop

    @cached_property
    def duration(self) -> Scalar:
        return self._sub_expr.duration[self.interval.start : self.interval.stop]
