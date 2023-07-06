from bloqade import start, cast

import numpy as np

from bokeh.plotting import figure, show

drive_frequency = 15
drive_amplitude = 15
min_time_step = 0.05

durations = cast(["ramp_time", "t_run", "ramp_time"])


def detuning_wf(t):
    return drive_amplitude * np.sin(drive_frequency * t)


floquet_program = (
    start.add_position((0, 0))
    .rydberg.rabi.amplitude.uniform.piecewise_linear(
        durations, [0, "rabi_max", "rabi_max", 0]
    )
    .detuning.uniform.fn(detuning_wf, sum(durations))
    .sample("min_time_step", "linear")
)

floquet_job = floquet_program.assign(
    ramp_time=0.06, min_time_step=0.05, rabi_max=15
).batch_assign(t_run=np.around(np.linspace(min_time_step, 3, 101), 13))
# have to start the time at 0.05 considering 0.03 (generated if we start at 0.0)
# is considered too small by validation

# submit to emulator
emu_job = floquet_job.braket_local_simulator(10000).submit().report()

# submit to HW
hw_job = (
    floquet_job.parallelize(24).braket(50).submit().save_json("example-1c-floquet.json")
)

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
    np.linspace(min_time_step, 3, 101),
    emu_job.rydberg_densities()[0].to_list(),
    line_width=2,
)

show(p)
