from bloqade.ir.location import Square

# create lattice
lattice = Square(4)

quantum_task = (
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
    .multiplex(10.0)
    .mock(10)
)

assert quantum_task.multiplex_mapping
