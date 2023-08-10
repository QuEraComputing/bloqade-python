from bloqade.ir import Sequence, rydberg, detuning, Uniform, Linear, ScaledLocations
from bloqade.ir.location import Square

# import bloqade.lattice as lattice

n_atoms = 11
lattice_const = 5.9

rabi_amplitude_values = [0.0, 15.8, 15.8, 0.0]
rabi_detuning_values = [-16.33, -16.33, "delta_end", "delta_end"]
durations = [0.8, "sweep_time", 0.8]

ordered_state_2D_prog = (
    Square(n_atoms, lattice_const)
    .rydberg.rabi.amplitude.uniform.piecewise_linear(durations, rabi_amplitude_values)
    .detuning.uniform.piecewise_linear(durations, rabi_detuning_values)
)

ordered_state_2D_job = ordered_state_2D_prog.assign(delta_end=42.66, sweep_time=2.4)

pbin = ordered_state_2D_job.quera(10)
# pbin.hardware_tasks[0].task_ir.show()


# dict interface
seq = Sequence(
    {
        rydberg: {
            detuning: {
                Uniform: Linear(start=1.0, stop="x", duration=3.0),
                ScaledLocations({1: 1.0, 2: 2.0}): Linear(
                    start=1.0, stop="x", duration=3.0
                ),
            },
        }
    }
)


# job = HardwareBatchResult.load_json("example-3-2d-ordered-state-job.json")

# res = job.report()


# print(lattice.Square(3).apply(seq).__lattice__)
# print(lattice.Square(3).apply(seq).braket(nshots=1000).submit().report().dataframe)
# print("bitstring")
# print(lattice.Square(3).apply(seq).braket(nshots=1000).submit().report().bitstring)

# # pipe interface
# report = (
#     lattice.Square(3)
#     .rydberg.detuning.uniform.apply(Linear(start=1.0, stop="x", duration=3.0))
#     .location(2)
#     .scale(3.0)
#     .apply(Linear(start=1.0, stop="x", duration=3.0))
#     .rydberg.rabi.amplitude.uniform
#     .apply(Linear(start=1.0, stop="x", duration=3.0))
#     .assign(x=10)
#     .braket(nshots=1000)
#     .submit()
#     .report()
# )

# print(report)
# print(report.bitstring)
# print(report.dataframe)

# lattice.Square(3).rydberg.detuning.location(2).location(3).apply(
#     Linear(start=1.0, stop="x", duration=3.0)
# ).location(3).location(4).apply(Linear(start=1.0, stop="x", duration=3.0)).braket(
#     nshots=1000
# ).submit()

# # start.rydberg.detuning.location(2).location(3)


# prog = (
#     lattice.Square(3)
#     .rydberg.detuning.uniform.apply(Linear(start=1.0, stop="x", duration=3.0))
#     .location(2)
#     .scale(3.0)
#     .apply(Linear(start=1.0, stop="x", duration=3.0))
#     .hyperfine.rabi.amplitude.location(2)
#     .apply(Linear(start=1.0, stop="x", duration=3.0))
#     .assign(x=1.0)
#     .multiplex(10.0).braket(nshots=1000)
#     .submit()
#     .report()
#     .dataframe.groupby(by=["x"])
#     .count()
# )

# (
#     lattice.Square(3)
#     .rydberg.detuning.uniform.apply(Linear(start=1.0, stop="x", duration=3.0))
#     .multiplex.quera
# )


# wf = (
#     Linear(start=1.0, stop=2.0, duration=2.0)
#     .scale(2.0)
#     .append(Linear(start=1.0, stop=2.0, duration=2.0))
# )


# prog = (
#     lattice.Square(3)
#     .hyperfine.detuning.location(1)
#     .scale(2.0)
#     .piecewise_linear(coeffs=[1.0, 2.0, 3.0])
#     .location(2)
#     .constant(value=2.0, duration="x")
# )

# prog.seq
# prog.lattice
