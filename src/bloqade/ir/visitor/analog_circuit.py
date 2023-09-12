import bloqade.ir.control.waveform as waveform
import bloqade.ir.control.field as field
import bloqade.ir.control.pulse as pulse
import bloqade.ir.control.sequence as sequence
import bloqade.ir.location.base as location
import bloqade.ir.analog_circuit as analog_circuit

from bloqade.ir.control.waveform import Waveform
from bloqade.ir.control.field import Field, SpatialModulation
from bloqade.ir.control.pulse import PulseExpr
from bloqade.ir.control.sequence import SequenceExpr
from bloqade.ir.location.base import AtomArrangement, ParallelRegister
from bloqade.ir.analog_circuit import AnalogCircuit
from typing import Union, Any


AstType = Union[
    Waveform,
    Field,
    SpatialModulation,
    PulseExpr,
    SequenceExpr,
    AtomArrangement,
    ParallelRegister,
    AnalogCircuit,
]


class AnalogCircuitVisitorV2:
    def visit_waveform(self, ast: waveform.Waveform) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__}"
            " for waveform.Waveform"
        )

    def visit_field(self, ast: field.Field) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} " "for field.Field"
        )

    def visit_uniform_modulation(self, ast: field.UniformModulation) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} "
            "for field.UniformModulation"
        )

    def visit_location(self, ast: field.Location) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} " "for field.Location"
        )

    def visit_scaled_locations(self, ast: field.ScaledLocations) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} "
            "for field.ScaledLocations"
        )

    def visit_run_time_vector(self, ast: field.RunTimeVector) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} "
            "for field.RunTimeVector"
        )

    def visit_assigned_run_time_vector(self, ast: field.AssignedRunTimeVector) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} "
            "for field.AssignedRunTimeVector"
        )

    def visit_pulse(self, ast: pulse.Pulse) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} " "for pulse.Pulse"
        )

    def visit_named_pulse(self, ast: pulse.NamedPulse) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} " "for pulse.NamedPulse"
        )

    def visit_append_pulse(self, ast: pulse.Append) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} " "for pulse.Append"
        )

    def visit_slice_pulse(self, ast: pulse.Slice) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} " "for pulse.Slice"
        )

    def visit_sequence(self, ast: sequence.Sequence) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} "
            "for sequence.Sequence"
        )

    def visit_named_sequence(self, ast: sequence.NamedSequence) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} "
            "for sequence.NamedSequence"
        )

    def visit_append_sequence(self, ast: sequence.Append) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} " "for sequence.Append"
        )

    def visit_slice_sequence(self, ast: sequence.Slice) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} " "for sequence.Slice"
        )

    def visit_register(self, ast: location.AtomArrangement) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} "
            "for location.AtomArrangement"
        )

    def visit_parallel_register(self, ast: location.ParallelRegister) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} "
            "for MultuplexRegister"
        )

    def visit_analog_circuit(self, ast: analog_circuit.AnalogCircuit) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} "
            "for analog_circuit.AnalogCircuit"
        )

    def visit(self, ast: AstType) -> Any:
        if isinstance(ast, waveform.Waveform):
            return self.visit_waveform(ast)
        elif isinstance(ast, field.UniformModulation):
            return self.visit_uniform_modulation(ast)
        elif isinstance(ast, field.Location):
            return self.visit_location(ast)
        elif isinstance(ast, field.ScaledLocations):
            return self.visit_scaled_locations(ast)
        elif isinstance(ast, field.RunTimeVector):
            return self.visit_run_time_vector(ast)
        elif isinstance(ast, field.AssignedRunTimeVector):
            return self.visit_assigned_run_time_vector(ast)
        elif isinstance(ast, field.Field):
            return self.visit_field(ast)
        elif isinstance(ast, pulse.Pulse):
            return self.visit_pulse(ast)
        elif isinstance(ast, pulse.NamedPulse):
            return self.visit_named_pulse(ast)
        elif isinstance(ast, pulse.Append):
            return self.visit_append_pulse(ast)
        elif isinstance(ast, pulse.Slice):
            return self.visit_slice_pulse(ast)
        elif isinstance(ast, sequence.Sequence):
            return self.visit_sequence(ast)
        elif isinstance(ast, sequence.NamedSequence):
            return self.visit_named_sequence(ast)
        elif isinstance(ast, sequence.Append):
            return self.visit_append_sequence(ast)
        elif isinstance(ast, sequence.Slice):
            return self.visit_slice_sequence(ast)
        elif isinstance(ast, location.AtomArrangement):
            return self.visit_register(ast)
        elif isinstance(ast, location.ParallelRegister):
            return self.visit_parallel_register(ast)
        elif isinstance(ast, analog_circuit.AnalogCircuit):
            return self.visit_analog_circuit(ast)
        else:
            raise NotImplementedError(
                f"No visitor method implemented in {self.__class__} for {type(ast)}"
            )


class AnalogCircuitVisitor:
    def visit_waveform(self, ast: Waveform) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for Waveform"
        )

    def visit_field(self, ast: Field) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for Field"
        )

    def visit_spatial_modulation(self, ast: SpatialModulation) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for SpatialModulation"
        )

    def visit_pulse(self, ast: PulseExpr) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for PulseExpr"
        )

    def visit_sequence(self, ast: SequenceExpr) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for SequenceExpr"
        )

    def visit_register(self, ast: AtomArrangement) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for AtomArrangement"
        )

    def visit_parallel_register(self, ast: ParallelRegister) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for MultuplexRegister"
        )

    def visit_analog_circuit(self, ast: AnalogCircuit) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for AnalogCircuit"
        )

    def visit(self, ast: AstType) -> Any:
        if isinstance(ast, Waveform):
            return self.visit_waveform(ast)
        elif isinstance(ast, SpatialModulation):
            return self.visit_spatial_modulation(ast)
        elif isinstance(ast, Field):
            return self.visit_field(ast)
        elif isinstance(ast, PulseExpr):
            return self.visit_pulse(ast)
        elif isinstance(ast, SequenceExpr):
            return self.visit_sequence(ast)
        elif isinstance(ast, AtomArrangement):
            return self.visit_register(ast)
        elif isinstance(ast, ParallelRegister):
            return self.visit_parallel_register(ast)
        elif isinstance(ast, AnalogCircuit):
            return self.visit_analog_circuit(ast)
        else:
            raise NotImplementedError(f"{ast.__class__} is not a bloqade AST type")
