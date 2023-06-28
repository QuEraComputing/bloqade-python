from bloqade import start

import numpy as np
import os
from bokeh.plotting import figure, show

plateau_time = (np.pi / 2 - 0.625) / 12.5
wf_durations = [0.05, plateau_time, 0.05, "t_run", 0.05, plateau_time, 0.05]
rabi_wf_values = [0.0, 12.5, 12.5, 0.0] * 2  # repeat values twice


ramsey_program = (
    start.add_position([0, 0])
    .rydberg.rabi.amplitude.uniform.piecewise_linear(wf_durations, rabi_wf_values)
    .detuning.uniform.piecewise_linear(wf_durations, [10.5] * (len(wf_durations) + 1))
)

ramsey_job = ramsey_program.batch_assign(t_run=np.around(np.arange(0, 30, 1) * 0.1, 13))

# run on emulator
emu_job = ramsey_job.braket_local_simulator(10000).submit().report()

# run on HW
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["AWS_ACCESS_KEY_ID"] = ""
os.environ["AWS_SECRET_ACCESS_KEY"] = ""
os.environ["AWS_SESSION_TOKEN"] = ""

hw_job = ramsey_job.parallelize(24).braket(100).submit()

# plot results
p = figure(
    x_axis_label="Time (us)",
    y_axis_label="Rydberg Density",
    tools="",
    toolbar_location=None,
)

p.axis.axis_label_text_font_size = "15pt"
p.axis.major_label_text_font_size = "10pt"

p.line(
    np.around(np.arange(0, 30, 1) * 0.1, 13),
    emu_job.rydberg_densities()[0].to_list(),
    line_width=2,
)
p.cross(
    np.around(np.arange(0, 30, 1) * 0.1, 13),
    emu_job.rydberg_densities()[0].to_list(),
    size=20,
)

show(p)
