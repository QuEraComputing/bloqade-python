from bloqade import start, cast

import numpy as np
from bokeh.layouts import row
from bokeh.plotting import show, figure

durations = ["ramp_time", "t_run", "ramp_time"]

noneq_dynamics_blockade_radius_program = (
    start.add_positions([(0, 0), (0, 8.5)])
    .rydberg.rabi.amplitude.uniform.piecewise_linear(
        durations, [0, "rabi_value", "rabi_value", 0]
    )
    .detuning.uniform.constant(0, sum(cast(durations)))
)

n_shots = 10000
run_times = 0.05 * np.arange(31)

noneq_dynamics_blockade_radius_job = noneq_dynamics_blockade_radius_program.assign(
    ramp_time=0.06, rabi_value=15
).batch_assign(t_run=run_times)

# submit to emulator
emu_job = (
    noneq_dynamics_blockade_radius_job.braket_local_simulator(n_shots).submit().report()
)

# submit to HW
hw_job = (
    noneq_dynamics_blockade_radius_job.parallelize(24)
    .braket(100)
    .submit()
    .save_json("example-2-nonequilibrium-dynamics-blockade-radius-job.json")
)

bitstring_dicts = emu_job.counts
zero_rydberg_probs = []  # "00"
one_rydberg_probs = []  # "01" or "10"
two_rydberg_probs = []  # "11"

for bitstring_dict in bitstring_dicts:
    zero_rydberg_probs.append(bitstring_dict.get("11", 0) / n_shots)
    one_rydberg_probs.append(
        (bitstring_dict.get("01", 0) + bitstring_dict.get("10", 0)) / n_shots
    )
    two_rydberg_probs.append(bitstring_dict.get("00", 0) / n_shots)

# make three separate plots

# "00" density
gg_density = figure(
    title="0 Rydberg",
    x_axis_label="Time (us)",
    y_axis_label="Rydberg Density",
    tools="",
    toolbar_location=None,
)

gg_density.axis.axis_label_text_font_size = "15pt"
gg_density.axis.major_label_text_font_size = "10pt"

gg_density.line(run_times, zero_rydberg_probs, line_width=2, color="green")


gr_rg_density = figure(
    title="1 Rydberg",
    x_axis_label="Time (us)",
    y_axis_label="Rydberg Density",
    tools="",
    toolbar_location=None,
)

gr_rg_density.axis.axis_label_text_font_size = "15pt"
gr_rg_density.axis.major_label_text_font_size = "10pt"

gr_rg_density.line(run_times, one_rydberg_probs, line_width=2, color="blue")


rr_density = figure(
    title="2 Rydberg",
    x_axis_label="Time (us)",
    y_axis_label="Rydberg Density",
    tools="",
    toolbar_location=None,
)

rr_density.axis.axis_label_text_font_size = "15pt"
rr_density.axis.major_label_text_font_size = "10pt"

rr_density.line(run_times, two_rydberg_probs, line_width=2, color="red")

p = row(gg_density, gr_rg_density, rr_density)

show(p)
