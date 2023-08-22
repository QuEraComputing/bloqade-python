import pytest
from bloqade.ir.location import Square
from bloqade import start


# create lattice
def test_parallel_task():
    lattice = Square(3, lattice_spacing=6)

    quantum_batch = (
        lattice.rydberg.detuning.uniform.piecewise_linear(
            durations=["up_time", "anneal_time", "up_time"],
            values=[
                "initial_detuning",
                "initial_detuning",
                "final_detuning",
                "final_detuning",
            ],
        )
        .rydberg.rabi.amplitude.uniform.piecewise_linear(
            durations=["up_time", "anneal_time", "up_time"],
            values=[0, "rabi_amplitude_max", "rabi_amplitude_max", 0],
        )
        .assign(
            initial_detuning=-10,
            up_time=0.1,
            final_detuning=15,
            anneal_time=10,
            rabi_amplitude_max=15,
        )
        .parallelize(10.0)
        .quera.mock()
        .submit(shots=10)
    )

    assert quantum_batch.tasks[0].task_data.parallel_decoder


def test_error_parallel_noatom():
    with pytest.raises(ValueError):
        start.rydberg.detuning.uniform.piecewise_linear(
            durations=["up_time", "anneal_time", "up_time"],
            values=[
                "initial_detuning",
                "initial_detuning",
                "final_detuning",
                "final_detuning",
            ],
        ).parallelize(10.0).quera.mock().submit(shots=1)
