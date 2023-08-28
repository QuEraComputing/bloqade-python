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
para_reg = prog.parse_register()
seq = prog.parse_sequence()
prog2 = start.rydberg.detuning.location(1).scale(2).piecewise_constant([0.1], [0.1])
seq2 = prog2.parse_sequence()


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
    pulse = seq.pulses[rydberg]
    with pytest.raises(NotImplementedError):
        pvis.visit(pulse)

    # field:
    field = seq.pulses[rydberg].fields[detuning]
    with pytest.raises(NotImplementedError):
        pvis.visit(field)

    # SpacialModu
    scaled_loc = list(seq2.pulses[rydberg].fields[Detuning()].value.keys())[0]
    with pytest.raises(NotImplementedError):
        pvis.visit(scaled_loc)


def test_get_natoms():
    prog = (
        Square(5)
        .rydberg.detuning.uniform.piecewise_linear(
            [0.1, 0.9, 0.1],
            [
                -10,
                -10,
                10,
                10,
            ],
        )
        .hyperfine.detuning.uniform.piecewise_linear(
            [0.1, 0.9, 0.1],
            [
                -10,
                -10,
                10,
                10,
            ],
        )
    )

    assert prog.n_atoms == 25
