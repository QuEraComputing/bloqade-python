from bloqade.codegen.common.assignment_scan import AssignmentScan
from bloqade.ir.location.base import AtomArrangement, SiteFilling
from bloqade.ir.visitor.analog_circuit import AnalogCircuitVisitor
from bloqade.ir.visitor.waveform import WaveformVisitor
from bloqade.ir.control.field import (
    Field,
    ScaledLocations,
    SpatialModulation,
    RunTimeVector,
    UniformModulation,
)
import bloqade.ir.scalar as scalar
import bloqade.ir.control.sequence as sequence
import bloqade.ir.control.pulse as pulse
import bloqade.ir.control.waveform as waveform
import bloqade.ir.control.field as field
import bloqade.ir as ir

from bloqade.emulate.ir.space import Space, TwoLevelAtom, ThreeLevelAtom
from bloqade.emulate.ir.emulator import (
    DetuningTerm,
    EmulatorProgram,
    LaserCoupling,
    RabiTerm,
)

import dataclasses
from typing import Any, Dict, Optional, Union, List
from numbers import Number, Real
from decimal import Decimal

ParamType = Union[Real, List[Real]]


@dataclasses.dataclass(frozen=True)
class WaveformScanResults:
    module_imports: Dict[str, str] = dataclasses.field(default_factory=dict)
    primative_exprs: Dict[str, str] = dataclasses.field(default_factory=dict)
    primative_tokens: Dict[str, str] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class WaveformScan(WaveformVisitor):
    var_number: int = 0
    shift: scalar.Scalar = ir.cast(0.0)
    assignments: Dict[str, ParamType] = dataclasses.field(default_factory=dict)
    module_imports: Dict[str, str] = dataclasses.field(default_factory=dict)
    primative_exprs: Dict[str, str] = dataclasses.field(default_factory=dict)
    primative_tokens: Dict[str, str] = dataclasses.field(default_factory=dict)

    def gensymm(self):
        self.var_number += 1
        return f"var{self.var_number}"

    @property
    def t(self) -> None:
        return str(ir.cast("t") + self.shift)

    def gen_token(self, expr: str) -> None:
        if expr not in self.primative_exprs:
            token = self.gensymm()
            self.primative_exprs[expr] = token
            self.primative_tokens[token] = expr

    def visit_constant(self, ast: waveform.Constant) -> None:
        pass

    def visit_linear(self, ast: waveform.Linear) -> None:
        start = ast.start(**self.assignments)
        stop = ast.stop(**self.assignments)
        duration = ast.duration(**self.assignments)
        slope = (stop - start) / duration
        if slope == 0:
            expr = f"{start!s}"
        elif slope == Decimal("1"):
            expr = f"({self.t!s} + {start!s})"
        else:
            expr = f"({slope!s} * {self.t!s} + {start!s})"
        self.gen_token(expr)

    def visit_poly(self, ast: waveform.Poly) -> None:
        coeff_str_list = [
            str(coeff(**self.assignments)) for coeff in ast.checkpoints[::-1]
        ]
        coeff_literal = f"[{','.join(coeff_str_list)}]"
        expr = f"np.polyval({coeff_literal}, {self.t})"
        self.gen_token(expr)

    def visit_python_fn(self, ast: waveform.PythonFn) -> None:
        import inspect

        module_name = inspect.getmodule(ast.fn).__name__

        if module_name != "__main__":
            # if function is coming from an external module that is not in `__main__`.
            # keep track of where function is imported from to fix any namespace issues
            # when generating the code for this function.
            self.module_imports[module_name] = ast.fn.__name__

        expr = f"{ast.fn.__name__}({self.t})"
        self.gen_token(expr)

    def visit_negative(self, ast: waveform.Negative) -> None:
        self.visit(ast.waveform)

    def visit_scale(self, ast: waveform.Scale) -> None:
        self.visit(ast.waveform)

    def visit_add(self, ast: waveform.Add) -> None:
        self.visit(ast.left)
        self.visit(ast.right)

    def visit_record(self, ast: waveform.Record) -> None:
        self.visit(ast.waveform)

    def visit_sample(self, ast: waveform.Sample) -> None:
        pass

    def visit_append(self, ast: waveform.Append) -> None:
        original_shift = self.shift
        for wf in ast.waveforms:
            self.visit(wf)
            self.shift += wf.duration(**self.assignments)
        self.shift = original_shift

    def visit_slice(self, ast: waveform.Slice) -> Any:
        self.shift += ast.interval.start(**self.assignments)
        self.visit(ast.waveform)
        self.shift -= ast.interval.start(**self.assignments)

    @staticmethod
    def scan(ast: waveform.Waveform, **assignments) -> "WaveformScanResults":
        assignments = AssignmentScan(assignments).emit(ast)
        scanner = WaveformScan(assignments=assignments)
        scanner.visit(ast)

        return WaveformScanResults(
            module_imports=scanner.module_imports,
            primative_exprs=scanner.primative_exprs,
            primative_tokens=scanner.primative_tokens,
        )


class WaveformCompiler(WaveformVisitor):
    # TODO: implement AST generator for waveforms.

    def __init__(self, assignments: Dict[str, Number]):
        self.assignments = assignments

    def emit(self, ast: waveform.Waveform):
        # fall back on interpreter for now.
        return lambda t: ast(t, **self.assignments)



class EmulatorProgramCodeGen(AnalogCircuitVisitor):
    def __init__(
        self, add_hyperfine: bool = False, assignments: Dict[str, Number] = {}, blockade_radius: float = 0.0
    ):
        self.add_hyperfine = add_hyperfine
        self.assignments = assignments
        self.waveform_compiler = WaveformCompiler(assignments)
        self.blockade_radius = blockade_radius
        self.space = None
        self.register = None
        self.duration = 0.0
        self.rydberg = None
        self.hyperfine = None

    def visit_program(self, ast: ir.AnalogCircuit):
        self.add_hyperfine = sequence.hyperfine in ast.sequence.pulses or self.add_hyperfine
        self.visit(ast.register)
        self.visit(ast.sequence)


    def visit_register(self, ast: AtomArrangement) -> Any:
        atom_positions = []
        for loc_info in ast.enumerate():
            if loc_info.filling == SiteFilling.filled:
                positions = tuple(
                    [pos(**self.assignments) for pos in loc_info.position]
                )
                atom_positions.append(positions)

        if self.add_hyperfine:
            self.space = Space.create(
                atom_positions,
                ThreeLevelAtom,
                blockade_radius=self.blockade_radius,
            )
        else:
            self.space = Space.create(
                atom_positions,
                TwoLevelAtom,
                blockade_radius=self.blockade_radius,
            )

    def visit_sequence(self, ast: sequence.SequenceExpr):
        match ast:
            case sequence.Sequence(pulses):
                for level_coupling, sub_pulse in pulses.items():
                    self.visit(sub_pulse)
                    match level_coupling:
                        case sequence.rydberg:
                            self.rydberg = LaserCoupling(
                                level_coupling=level_coupling,
                                detuning=self.detuning_terms,
                                rabi=self.rabi_terms,
                            )
                        case sequence.hyperfine:
                            self.hyperfine = LaserCoupling(
                                level_coupling=level_coupling,
                                detuning=self.detuning_terms,
                                rabi=self.rabi_terms,
                            )

            case sequence.NamedSequence(sub_sequence, _):
                self.visit(sub_sequence)

            case _:
                raise NotImplementedError

    def visit_spatial_modulation(self, ast: SpatialModulation) -> Dict[int, float]:
        match ast:
            case UniformModulation():
                return {atom: 1.0 for atom in range(self.space.n_atoms)}
            case RunTimeVector(name):
                return {
                    atom: coeff for atom, coeff in enumerate(self.assignments[name])
                }
            case ScaledLocations(locations):
                return {
                    loc.value: float(coeff(**self.assignments))
                    for loc, coeff in locations.items()
                }

    def visit_detuning(self, ast: Optional[Field]):
        if ast is None:
            return []

        terms = []

        match ast:
            case Field(value) if len(value) < self.space.n_atoms:
                for sm, wf in value.items():
                    self.duration = max(
                        float(wf.duration(**self.assignments)), self.duration
                    )
                    terms.append(
                        DetuningTerm(
                            target_atoms=self.visit_spatial_modulation(sm),
                            amplitude=self.waveform_compiler.emit(wf),
                        )
                    )

            case Field(value):
                target_atom_dict = {
                    sm: self.visit_spatial_modulation(sm) for sm in value.keys()
                }

                for atom in range(self.space.n_atoms):
                    wf = sum(
                        (
                            target_atom_dict[sm].get(atom, 0.0) * wf
                            for sm, wf in value.items()
                        ),
                        start=waveform.Constant(0.0, 0.0),
                    )
                    self.duration = max(
                        float(wf.duration(**self.assignments)), self.duration
                    )

                    terms.append(
                        DetuningTerm(
                            target_atoms={atom: 1},
                            amplitude=self.waveform_compiler.emit(wf),
                        )
                    )

        return terms

    def visit_rabi(self, amplitude: Optional[Field], phase: Optional[Field]):
        terms = []
        match (amplitude, phase):
            case (None, _):
                return []

            case (Field(value), None) if len(value) < self.space.n_atoms:
                for sm, wf in value.items():
                    self.duration = max(
                        float(wf.duration(**self.assignments)), self.duration
                    )
                    terms.append(
                        RabiTerm(
                            target_atoms=self.visit_spatial_modulation(sm),
                            amplitude=self.waveform_compiler.emit(wf),
                        )
                    )

            case (
                Field(value),
                Field(value={field.Uniform: phase_waveform}),
            ) if len(value) < self.space.n_atoms:
                rabi_phase = self.waveform_compiler.emit(phase_waveform)
                self.duration = max(
                    float(phase_waveform.duration(**self.assignments)), self.duration
                )
                for sm, wf in value.items():
                    self.duration = max(
                        float(wf.duration(**self.assignments)), self.duration
                    )
                    terms.append(
                        RabiTerm(
                            target_atoms=self.visit_spatial_modulation(sm),
                            amplitude=self.waveform_compiler.emit(wf),
                            phase=rabi_phase,
                        )
                    )

            case _:  # fully local fields
                phase_target_atoms_dict = {
                    sm: self.visit_spatial_modulation(sm) for sm in phase.value.keys()
                }
                phase_target_atoms_dict = {
                    sm: self.visit_spatial_modulation(sm)
                    for sm in amplitude.value.keys()
                }

                terms = []
                for atom in range(self.space.n_atoms):
                    phase_wf = sum(
                        (
                            phase_target_atoms_dict[sm].get(atom, 0.0) * wf
                            for sm, wf in phase.value.items()
                        ),
                        start=waveform.Constant(0.0, 0.0),
                    )
                    amplitude_wf = sum(
                        (
                            phase_target_atoms_dict[sm].get(atom, 0.0) * wf
                            for sm, wf in amplitude.value.items()
                        ),
                        start=waveform.Constant(0.0, 0.0),
                    )

                    self.duration = max(
                        float(phase_wf.duration(**self.assignments)), self.duration
                    )
                    self.duration = max(
                        float(amplitude_wf.duration(**self.assignments)), self.duration
                    )

                    terms.append(
                        RabiTerm(
                            target_atoms={atom: 1},
                            amplitude=self.waveform_compiler.emit(amplitude_wf),
                            phase=self.waveform_compiler.emit(phase_wf),
                        )
                    )

    def visit_pulse(self, ast: pulse.PulseExpr):
        match ast:
            case pulse.Pulse(fields):
                detuning = fields.get(pulse.detuning, None)
                amplitude = fields.get(pulse.rabi.amplitude, None)
                phase = fields.get(pulse.rabi.phase, None)

                self.detuning_terms = self.visit_detuning(detuning)
                self.rabi_terms = self.visit_rabi(amplitude, phase)

            case pulse.NamedPulse(sub_pulse, _):
                self.visit(sub_pulse)

            case _:
                raise NotImplementedError

    def emit(self, circuit: ir.AnalogCircuit) -> EmulatorProgram:
        self.assignments = AssignmentScan(self.assignments).emit(circuit.sequence)
        
        self.visit(circuit)
        return EmulatorProgram(
            space=self.space,
            duration=self.duration,
            rydberg=self.rydberg,
            hyperfine=self.hyperfine,
        )
