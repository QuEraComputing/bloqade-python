from bloqade.ir.batch import BloqadeBatch, BloqadeTask
from bloqade.ir.program import BloqadeProgram
from collections import OrderedDict
from typing import Tuple
from numbers import Real


class LowerBloqadeProgram:
    """Lower from BloqadeProgram to BloqadeBatch."""

    def __init__(self, program: BloqadeProgram):
        self.program = program

    def compile(self, args: Tuple[Real, ...]) -> BloqadeBatch:
        from bloqade.codegen.common.static_assign import StaticAssignProgram

        tasks = OrderedDict()
        for task_number, assignments in enumerate(
            self.program.params.batch_assignments(*args)
        ):
            circuit = StaticAssignProgram(assignments).visit(self.program.circuit)
            tasks[task_number] = BloqadeTask(circuit, assignments)

        return BloqadeBatch(self.program, tasks)
