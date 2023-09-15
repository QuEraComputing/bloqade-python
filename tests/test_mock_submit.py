import bloqade.ir.location as location
from bloqade.ir import Linear, Constant
from bloqade.serialize import loads, dumps


def test():
    batch = (
        location.Square(6)
        .rydberg.detuning.uniform.apply(
            Constant("initial_detuning", "up_time")
            .append(Linear("initial_detuning", "final_detuning", "anneal_time"))
            .append(Constant("final_detuning", "up_time"))
        )
        .rabi.amplitude.uniform.apply(
            Linear(0.0, "rabi_amplitude_max", "up_time")
            .append(Constant("rabi_amplitude_max", "anneal_time"))
            .append(Linear("rabi_amplitude_max", 0.0, "up_time"))
        )
        .assign(
            initial_detuning=-10,
            up_time=0.1,
            final_detuning=15,
            anneal_time=10,
            rabi_amplitude_max=15,
        )
        .quera.mock()
        ._compile(shots=10)
    )

    batch_str = dumps(batch)
    assert isinstance(loads(batch_str), type(batch))
