from dataclasses import dataclass
from typing import Dict, List, Optional, Callable

from bloqade.ir.control.sequence import LevelCoupling
from bloqade.emulate.ir.space import Space


@dataclass(frozen=True)
class RabiTerm:
    target_atoms: Dict[int, float]
    amplitude: Callable[[float], float]
    phase: Optional[Callable[[float], float]] = None


@dataclass(frozen=True)
class DetuningTerm:
    target_atoms: Dict[int, float]
    amplitude: Callable[[float], float]


@dataclass(frozen=True)
class LaserCoupling:
    level_coupling: LevelCoupling
    detuning: List[DetuningTerm]
    rabi: List[RabiTerm]


@dataclass(frozen=True)
class EmulatorProgram:
    space: Space
    duration: float
    rydberg: Optional[LaserCoupling] = None
    hyperfine: Optional[LaserCoupling] = None


class Visitor:
    def visit_emulator_program(self, ast):
        raise NotImplementedError

    def visit_laser_coupling(self, ast):
        raise NotImplementedError

    def visit_detuning_term(self, ast):
        raise NotImplementedError

    def visit_rabi_term(self, ast):
        raise NotImplementedError

    def visit_space(self, ast):
        raise NotImplementedError

    def visit(self, ast):
        match ast:
            case EmulatorProgram():
                return self.visit_emulator_program(ast)
            case Space():
                return self.visit_space(ast)
            case LaserCoupling():
                return self.visit_laser_coupling(ast)
            case DetuningTerm():
                return self.visit_detuning_term(ast)
            case RabiTerm():
                return self.visit_rabi_term(ast)
