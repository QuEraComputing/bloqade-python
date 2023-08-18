from bloqade.ir.location import Square
import pytest


def test_braket_unsupport_parallel():
    prog = Square(3)

    prog = prog.rydberg.detuning.uniform.piecewise_constant([0.1], [32])
    prog = prog.parallelize(4)

    with pytest.raises(TypeError):
        prog.braket.local_simulator()
