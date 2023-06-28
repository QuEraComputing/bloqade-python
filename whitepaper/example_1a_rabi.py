from bloqade import start

import numpy as np
from bokeh.plotting import figure, show

import os

durations = ["ramp_time", "run_time", "ramp_time"]

rabi_oscillations_program = (
    start.add_position((0, 0))
    .rydberg.rabi.amplitude.uniform.piecewise_linear(
        durations=durations, values=[0, "rabi_value", "rabi_value", 0]
    )
    .detuning.uniform.piecewise_linear(
        durations=durations, values=[0, "detuning_value", "detuning_value", 0]
    )
)

rabi_oscillation_job = rabi_oscillations_program.assign(
    ramp_time=0.06, rabi_value=15, detuning_value=0.0
).batch_assign(run_time=np.around(np.arange(0, 21, 1) * 0.05, 13))

# contains 21 tasks as consequence of batch_assign
# currently not exactly reproducible over run_time = 0 issue and
# non-monotonically increasing durations that Braket validation expects

# HW results
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["AWS_ACCESS_KEY_ID"] = ""
os.environ["AWS_SECRET_ACCESS_KEY"] = ""
os.environ["AWS_SESSION_TOKEN"] = ""

# Can be saved as JSON and later reloaded when results are available
hw_job = rabi_oscillation_job.parallelize(24).braket(100).submit()

# Simulation Results
emu_job = rabi_oscillation_job.braket_local_simulator(10000).submit().report()

p = figure(
    x_axis_label="Time (us)",
    y_axis_label="Rydberg Density",
    toolbar_location=None,
    tools="",
)

p.axis.axis_label_text_font_size = "15pt"
p.axis.major_label_text_font_size = "10pt"

p.line(
    np.around(np.arange(0, 21, 1) * 0.05, 13),
    emu_job.rydberg_densities()[0].to_list(),
    line_width=2,
)
p.cross(
    np.around(np.arange(0, 21, 1) * 0.05, 13),
    emu_job.rydberg_densities()[0].to_list(),
    size=20,
)

show(p)
