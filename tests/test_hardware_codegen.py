# from bloqade import start
from bloqade.ir import location
from bloqade.ir import Constant, Linear, Poly
import pytest
import json


def test_integration_jump_err():
    ## jump at the end of linear -- constant
    with pytest.raises(ValueError):
        (
            location.Square(6)
            .rydberg.detuning.uniform.apply(
                Constant("initial_detuning", "up_time")
                .append(Linear("initial_detuning", "final_detuning", "anneal_time"))
                .append(0.5 * Constant("final_detuning", "up_time"))
            )
            .assign(
                initial_detuning=-10,
                up_time=0.1,
                final_detuning=15,
                anneal_time=10,
            )
            .mock(10)
        )


def test_integration_scale():
    seq = Linear(start=0.0, stop=1.0, duration=0.5).append(
        2 * Constant(0.5, duration=0.5)
    )
    job = location.Square(1).rydberg.detuning.uniform.apply(seq).mock(10)

    panel = json.loads(job.json())

    print(panel)


def test_integration_neg():
    seq = Linear(start=0.0, stop=-0.5, duration=0.5).append(
        -Constant(0.5, duration=0.5)
    )
    job = location.Square(1).rydberg.detuning.uniform.apply(seq).mock(10)

    panel = json.loads(job.json())
    print(panel)


def test_integration_poly_order_err():
    ## poly
    with pytest.raises(ValueError):
        seq = Poly(checkpoints=[1, 2, 3], duration=0.5).append(
            -Constant(0.5, duration=0.5)
        )
        (location.Square(1).rydberg.detuning.uniform.apply(seq).mock(10))


def test_integration_poly_const():
    ## constant
    seq = Poly(checkpoints=[1], duration=0.5).append(Constant(1, duration=0.5))
    job = location.Square(1).rydberg.detuning.uniform.apply(seq).mock(10)

    panel = json.loads(job.json())
    print(panel)


def test_integration_poly_linear():
    ## linear
    seq = Poly(checkpoints=[1, 2], duration=0.5).append(Constant(2, duration=0.5))
    job = location.Square(1).rydberg.detuning.uniform.apply(seq).mock(10)

    panel = json.loads(job.json())
    print(panel)
