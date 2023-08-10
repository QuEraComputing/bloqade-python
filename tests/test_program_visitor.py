# from bloqade import start
from bloqade import start
from bloqade.ir import rydberg, detuning
from bloqade.ir.location import Square
from bloqade.ir.visitor.program import ProgramVisitor
from bloqade.ir.control.waveform import Linear
from bloqade.ir.control.pulse import Detuning
import pytest


wv_linear = Linear(start=0, stop=4, duration=0.1)
reg = Square(3)
prog = reg.rydberg.detuning.uniform.piecewise_constant([0.1], [0.1]).parallelize(10.0)
para_reg = prog.register
seq = prog.sequence
prog2 = start.rydberg.detuning.location(1).scale(2).piecewise_constant([0.1], [0.1])
seq2 = prog2.sequence


def test_base_program_visitor():
    pvis = ProgramVisitor()

    # waveform
    with pytest.raises(NotImplementedError):
        pvis.visit(wv_linear)

    # registor
    with pytest.raises(NotImplementedError):
        pvis.visit(reg)

    # parallel reg
    with pytest.raises(NotImplementedError):
        pvis.visit(para_reg)

    # sequence
    with pytest.raises(NotImplementedError):
        pvis.visit(seq)

    # pulse:
    pulse = seq.value[rydberg]
    with pytest.raises(NotImplementedError):
        pvis.visit(pulse)

    # field:
    field = seq.value[rydberg].value[detuning]
    with pytest.raises(NotImplementedError):
        pvis.visit(field)

    # SpacialModu
    scaled_loc = list(seq2.value[rydberg].value[Detuning()].value.keys())[0]
    with pytest.raises(NotImplementedError):
        pvis.visit(scaled_loc)
