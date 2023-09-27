from beartype.typing import List, Dict, Union, TYPE_CHECKING
from bloqade.builder.typing import LiteralType, ParamType
from bloqade.ir.scalar import Variable

if TYPE_CHECKING:
    from bloqade.builder.assign import Assign, BatchAssign, ListAssign
    from bloqade.builder.parallelize import Parallelize
    from bloqade.builder.args import Args


class AddArgs:
    def args(self, args_list: List[Union[str, Variable]]) -> "Args":
        from bloqade.builder.args import Args

        return Args(args_list, self)


class Assignable:
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
            ...       .add_position([(0,0),(1,1),(2,2),(3,3)])
            >>> seq = reg.rydberg.detuning.uniform
            ...       .linear(start="ival",stop=1,duration="span_time")
            >>> seq = seq.assign(span_time = 0.5, ival = 0.0)

        """
        from bloqade.builder.assign import Assign

        return Assign(assignments, parent=self)


class BatchAssignable:
    def batch_assign(
        self,
        __batch_params: List[Dict[str, ParamType]] = [],
        **assignments: List[ParamType],
    ) -> Union["BatchAssign", "ListAssign"]:
        from bloqade.builder.assign import BatchAssign, ListAssign

        if len(__batch_params) > 0 and assignments:
            raise ValueError("batch_params and assignments cannot be used together.")

        if len(__batch_params) > 0:
            return ListAssign(__batch_params, parent=self)
        else:
            return BatchAssign(assignments, parent=self)


class Parallelizable:
    def parallelize(self, cluster_spacing: LiteralType) -> "Parallelize":
        """
        Parallelize the current problem (register & sequnece) to fill entire FOV
        with the given cluster spacing.

        Args:
            cluster_spacing (Real | Decimal):
            the spacing between parallel clusters.

        Examples:
            - Parallelize the current problem with cluster spacing 7.2 um.

            >>> prob = (
                    bloqade.start.add_position([(0,0),(1,1),(2,2),(3,3)])
                    .rydberg.detuning.uniform
                    .linear(start=0,stop=1,duration=1)
                    )
            >>> prob = prob.parallelize(7.2)

        """
        from bloqade.builder.parallelize import Parallelize

        return Parallelize(cluster_spacing, self)
