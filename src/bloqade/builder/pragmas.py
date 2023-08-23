from .base import Builder
from typing import Any, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .parallelize import Parallelize, ParallelizeFlatten
    from .assign import Assign, BatchAssign
    from .flatten import Flatten


class Flattenable(Builder):
    def flatten(self, orders: List[str]) -> "Flatten":
        from .flatten import Flatten

        return Flatten(orders, self)


class Assignable(Builder):
    def assign(self, **assignments) -> "Assign":
        """
        Assign values to variables declared previously in the program.

        Args:
            assignments (Dict[str, Union[Number]]):
            The assignments, which should be a kwargs
            where the key is the variable name and the
            value is the value to assign to the variable.

        Examples:
            - Assign the value 0.0 to the variable "ival"
            and 0.5 to the variable "span_time".

            >>> reg = bloqade.start
            ...       .add_positions([(0,0),(1,1),(2,2),(3,3)])
            >>> seq = reg.rydberg.detuning.uniform
            ...       .linear(start="ival",stop=1,duration="span_time")
            >>> seq = seq.assign(span_time = 0.5, ival = 0.0)

        """
        from .assign import Assign

        return Assign(parent=self, **assignments)


class BatchAssignable(Builder):
    def batch_assign(self, **assignments) -> "BatchAssign":
        from .assign import BatchAssign

        return BatchAssign(parent=self, **assignments)


class Parallelizable(Builder):
    def parallelize(self, cluster_spacing: Any) -> "Parallelize":
        """
        Parallelize the current problem (register & sequnece) to fill entire FOV
        with the given cluster spacing.

        Args:
            cluster_spacing (Any, should be Real):
            the spacing between parallel clusters.

        Examples:
            - Parallelize the current problem with cluster spacing 7.2 um.

            >>> prob = (
                    bloqade.start.add_positions([(0,0),(1,1),(2,2),(3,3)])
                    .rydberg.detuning.uniform
                    .linear(start=0,stop=1,duration=1)
                    )
            >>> prob = prob.parallelize(7.2)

        """
        from .parallelize import Parallelize

        return Parallelize(cluster_spacing, self)


class FlattenParallelizable(Builder):
    def parallelize(self, cluster_spacing: Any) -> "ParallelizeFlatten":
        """
        Parallelize the current problem (register & sequnece) to fill entire FOV
        with the given cluster spacing.

        Args:
            cluster_spacing (Any, should be Real):
            the spacing between parallel clusters.

        Examples:
            - Parallelize the current problem with cluster spacing 7.2 um.

            >>> prob = (
                    bloqade.start.add_positions([(0,0),(1,1),(2,2),(3,3)])
                    .rydberg.detuning.uniform
                    .linear(start=0,stop=1,duration=1)
                    )
            >>> prob = prob.parallelize(7.2)

        """
        from .parallelize import Parallelize

        return Parallelize(cluster_spacing, self)
