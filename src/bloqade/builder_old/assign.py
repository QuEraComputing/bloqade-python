from .base import Builder


class Assign(Builder):
    def __init__(self, parent: Builder, **assignments) -> None:
        super().__init__(parent)
        self._assignments = assignments

    def batch_assign(self, **assignments) -> "BatchAssign":
        return BatchAssign(self, **assignments)


class BatchAssign(Builder):
    def __init__(self, parent: Builder, **assignments) -> None:
        super().__init__(parent)
        self._assignments = assignments

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
        return Assign(self, **assignments)
