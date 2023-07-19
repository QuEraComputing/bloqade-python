from bloqade.ir.location import Square
import pytest
import json


def test_braket_unsupport_parallel():
    prog = Square(3)

    prog = prog.rydberg.detuning.uniform.piecewise_constant([0.1], [32])
    prog = prog.parallelize(4)

    with pytest.raises(TypeError):
        prog.braket_local_simulator(10)


def test_in_house_simulator_entry():
    prog = Square(3)

    prog = prog.rydberg.detuning.uniform.piecewise_constant([0.1], [32])
    prog = prog.parallelize(4)

    with pytest.raises(NotImplementedError):
        prog.simu(4)


def test_braket():
    prog = Square(3)

    prog = prog.rydberg.detuning.uniform.piecewise_constant([0.1], [32])

    job = prog.braket(4)

    x = json.loads(job.json())
    assert x["tasks"]["0"]["task_ir"]["nshots"] == 4
