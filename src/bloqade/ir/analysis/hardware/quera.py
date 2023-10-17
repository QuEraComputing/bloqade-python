from bloqade.ir.analysis.hardware.piecewise_linear import PiecewiseLinearValidator
from bloqade.ir.analysis.hardware.piecewise_constant import PiecewiseConstantValidator
from bloqade.ir.visitor.analog_circuit import AnalogCircuitVisitor
import bloqade.ir.control.sequence as sequence
import bloqade.ir.control.pulse as pulse
import bloqade.ir.control.field as field
import bloqade.ir.control.waveform as waveform
from builder.typing import LiteralType
from beartype.typeing import Dict



class AHSValidator(AnalogCircuitVisitor):
    def __init__(self, assignments: Dict[str, LiteralType] = {}):
        self.assignments = dict(assignments)


    def validate_detuning(self, detuning: field.Field):
        pass

    def validate_rabi_amp(self, rabi_amp: field.Field):
        pass

    def validate_rabi_phase(self, rabi_freq: field.Field):
        pass


    
