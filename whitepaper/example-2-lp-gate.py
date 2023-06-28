from bloqade import start

import numpy as np
from bokeh.layouts import row
from bokeh.plotting import figure, show

delta = 0.377371  # Detuning
xi = 3.90242  # Phase jump
tau = 4.29268  # Time of each pulse

amplitude_max = 10
min_time_step = 0.05
detuning_value = delta * amplitude_max
T = (
    tau / amplitude_max - min_time_step
)  # this T ends up being smaller than the minimum time step

durations = [
    min_time_step,
    T,
    min_time_step,
    min_time_step,
    min_time_step,
    T,
    min_time_step,
]
rabi_wf_values = [
    0.0,
    amplitude_max,
    amplitude_max,
    0.0,
    0.0,
    amplitude_max,
    amplitude_max,
    0.0,
]

lp_gate_sequence = (
    start.rydberg.rabi.amplitude.uniform.piecewise_linear(durations, rabi_wf_values)
    .slice(0, "t_run")
    .detuning.uniform.constant(detuning_value, sum(durations))
    .slice(0, "t_run")
    .phase.uniform.piecewise_constant(durations, [0.0] * 4 + [xi] * 3)
    .slice(0, "t_run")
    .sequence
)

run_times = np.arange(min_time_step, sum(durations), min_time_step)

# create a one atom and two atom example
atom_positions = [[(0, 0)], [(0, 0), (0, 4.0)]]

lp_gate_programs = []
for atom_position in atom_positions:
    lp_gate_programs.append(start.add_positions(atom_position).apply(lp_gate_sequence))

lp_gate_jobs = []
for lp_gate_program in lp_gate_programs:
    lp_gate_jobs.append(
        lp_gate_program.batch_assign(
            # not happy starting from t_run = 0.0, have to offset a little
            t_run=run_times
        )
    )

# submit to emulator
emu_jobs = []
for lp_gate_job in lp_gate_jobs:
    emu_jobs.append(lp_gate_job.braket_local_simulator(10000).submit().report())

# plot results
single_atom_lp = figure(
    title="Single Atom LP Gate",
    x_axis_label="Time (us)",
    y_axis_label="Rydberg Density",
    tools="",
    toolbar_location=None,
)

single_atom_lp.axis.axis_label_text_font_size = "15pt"
single_atom_lp.axis.major_label_text_font_size = "10pt"

single_atom_lp.line(run_times, emu_jobs[0].rydberg_densities()[0], line_width=2)

dual_atom_lp = figure(
    title="Dual Atom LP Gate",
    x_axis_label="Time (us)",
    y_axis_label="Rydberg Density",
    tools="",
    toolbar_location=None,
)

dual_atom_lp.axis.axis_label_text_font_size = "15pt"
dual_atom_lp.axis.major_label_text_font_size = "10pt"

dual_atom_lp.line(
    run_times, emu_jobs[1].rydberg_densities()[0], line_width=2, legend_label="Atom 1"
)
dual_atom_lp.line(
    run_times,
    emu_jobs[1].rydberg_densities()[1],
    line_width=2,
    color="red",
    legend_label="Atom 2",
)

p = row(single_atom_lp, dual_atom_lp)

show(p)
