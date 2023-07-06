from bloqade.ir.location import Chain
import numpy as np

from bokeh.plotting import figure, show

n_atoms = 11
lattice_const = 6.1
min_time_step = 0.05

rabi_amplitude_values = [0.0, 15.8, 15.8, 0.0]
rabi_detuning_values = [-16.33, -16.33, 16.33, 16.33]
durations = [0.8, "sweep_time", 0.8]

time_sweep_z2_prog = (
    Chain(n_atoms, lattice_const)
    .rydberg.rabi.amplitude.uniform.piecewise_linear(durations, rabi_amplitude_values)
    .detuning.uniform.piecewise_linear(durations, rabi_detuning_values)
)

time_sweep_z2_job = time_sweep_z2_prog.batch_assign(
    sweep_time=np.linspace(min_time_step, 2.4, 20)
)  # starting at 0.0 not feasible, just use min_time_step

emu_job = time_sweep_z2_job.braket_local_simulator(10000).submit().report()

hw_job = (
    time_sweep_z2_job.parallelize(lattice_const * 3)
    .braket(100)
    .submit()
    .save_json("example-3-time-sweep-job.json")
)

# 20 different measurements taken, need to calculate probability of Z_2 state per each
time_sweep_z2_probabilities = []

for bitstring_counts in emu_job.counts:
    z2_probability = bitstring_counts["01010101010"] / sum(
        list(bitstring_counts.values())
    )
    time_sweep_z2_probabilities.append(z2_probability)


p = figure(
    x_axis_label="Annealing time (us)",
    y_axis_label="Z_2 state probability",
    toolbar_location=None,
    tools="",
)

p.line(list(np.linspace(0.1, 2.4, 20)), time_sweep_z2_probabilities, line_width=2)

show(p)
