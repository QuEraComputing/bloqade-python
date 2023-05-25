from bloqade.ir.location import Square

# create lattice
lattice = Square(3, lattice_spacing=6)

quantum_task = (
    lattice.parallelize(10.0)
    .rydberg.detuning.uniform.piecewise_linear(
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
    .mock(10)
)

assert quantum_task.tasks[0].parallel_decoder
