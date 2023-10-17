from typing import Any
import bloqade.ir.analog_circuit as analog_circuit
from bloqade.ir.analysis.hardware.piecewise_linear import PiecewiseLinearValidator, PiecewiseLinearValidatorResults
from bloqade.ir.analysis.hardware.piecewise_constant import PiecewiseConstantValidator
import bloqade.ir.location.base as location
from bloqade.ir.visitor.analog_circuit import AnalogCircuitVisitor
import bloqade.ir.control.sequence as sequence
import bloqade.ir.control.pulse as pulse
import bloqade.ir.control.field as field
import bloqade.ir.control.waveform as waveform
import bloqade.ir.location as location
from bloqade.builder.typing import LiteralType
from beartype.typing import Dict
from pydantic.dataclasses import dataclass


@dataclass
class AHSValidatorResult:
    detuning_value: PiecewiseLinearValidatorResults


class AHSValidator(AnalogCircuitVisitor):
    def __init__(self, assignments: Dict[str, LiteralType] = {}):
        self.assignments = dict(assignments)


    @staticmethod
    def check_continuity(lhs: AHSValidatorResult, rhs:AHSValidatorResult) -> bool:


    def validate_detuning(self, detuning: field.Field):
        pass

    def validate_rabi_amplitude(self, rabi_amp: field.Field):
        pass

    def validate_rabi_phase(self, rabi_freq: field.Field):
        pass


    def visit_register(self, ast: location.AtomArrangement) -> Any:
        pass
    
    def visit_parallel_register(self, ast: location.ParallelRegister) -> Any:
        self.visit(ast._register)
    
    def visit_analog_circuit(self, ast: analog_circuit.AnalogCircuit) -> Any:
        self.visit(ast.register)
        self.visit(ast.sequence)
        
    def visit_pulse(self, ast: pulse.Pulse) -> Any:
        for field_name, fd in ast.fields.items():
            if field_name == pulse.detuning:
                self.validate_detuning(fd)
            elif field_name == pulse.rabi.amplitude:
                self.validate_rabi_amplitude(fd)
            elif field_name == pulse.rabi.phase:
                self.validate_rabi_phase(fd)
        
    def visit_append_pulse(self, ast: pulse.Append) -> Any:
        raise NotImplementedError(
            "AHS does not support compositions of pulses"
        )
        
    def visit_slice_pulse(self, ast: pulse.Slice) -> Any:
        raise NotImplementedError(
            "AHS does not support compositions of pulses"
        )
        
    def visit_named_pulse(self, ast: pulse.NamedPulse) -> Any:
        self.visit(ast.pulse)
        
    def visit_sequence(self, ast: sequence.Sequence) -> Any:
        if sequence.hyperfine in ast.pulses:
            raise ValueError(
                "AHS does not support hyperfine pulses"
            )
            
        self.visit(ast.pulses[sequence.rydberg])
        
    def visit_append_sequence(self, ast: sequence.Append) -> Any:
        result = 
