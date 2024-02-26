# from bloqade import start
from bloqade import start
from bloqade.ir.location import Square
from bloqade.ir.control.waveform import Linear


wv_linear = Linear(start=0, stop=4, duration=0.1)
reg = Square(3)
prog = reg.rydberg.detuning.uniform.piecewise_constant([0.1], [0.1]).parallelize(10.0)
para_reg = prog.parse_register()
seq = prog.parse_sequence()
prog2 = start.rydberg.detuning.location(1, 2).piecewise_constant([0.1], [0.1])
seq2 = prog2.parse_sequence()


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
