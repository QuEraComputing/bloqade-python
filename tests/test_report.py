from bloqade.ir.location import ListOfLocations
import tempfile

prog = (
    ListOfLocations()
    .add_position((0, 0))
    .add_position((0, 6))
    .add_position((0, 3))
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
        up_time=0.1,
        anneal_time=3.8,
        initial_detuning=-15,
        final_detuning=10,
        rabi_amplitude_max=15,
    )
)

with tempfile.NamedTemporaryFile() as f:
    future = prog.quera.mock(state_file=f.name).submit(shots=100)
    future.pull()

print(future.report().bitstrings)
print(future.report().counts)
print(future.report().dataframe)
print(future.report().rydberg_densities())
