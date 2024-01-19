from bloqade.core.ir.visitor import BloqadeIRTransformer
import bloqade.core.ir.scalar as scalar
from bloqade.core.ir.control import waveform


class AssignToLiteral(BloqadeIRTransformer):
    """Transform all assigned variables to literals."""

    def visit_scalar_AssignedVariable(self, node: scalar.AssignedVariable):
        return scalar.Literal(node.value)

    def visit_waveform_PythonFn(self, node: waveform.PythonFn):
        return node  # skip these nodes
