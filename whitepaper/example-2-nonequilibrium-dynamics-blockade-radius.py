from bloqade import start, cast
from bloqade.task import HardwareFuture

import numpy as np

from bokeh.layouts import row
from bokeh.plotting import show, figure
from bokeh.models import HoverTool, CrosshairTool, ColumnDataSource

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
"""
hw_job = (
    noneq_dynamics_blockade_radius_job.parallelize(24)
    .braket(100)
    .submit()
    .save_json("example-2-nonequilibrium-dynamics-blockade-radius-job.json")
)
"""
# get HW results back
hw_future = HardwareFuture()
hw_future.load_json("example-2-nonequilibrium-dynamics-blockade-radius-job.json")
hw_report = hw_future.report()


def generate_probabilities(report):
    zero_rydberg_probs = []  # "00"
    one_rydberg_probs = []  # "01" or "10"
    two_rydberg_probs = []  # "11"

    for bitstring_counts in report.counts:
        zero_rydberg_probs.append(bitstring_counts.get("11", 0) / n_shots)
        one_rydberg_probs.append(
            (bitstring_counts.get("01", 0) + bitstring_counts.get("10", 0)) / n_shots
        )
        two_rydberg_probs.append(bitstring_counts.get("00", 0) / n_shots)

    return zero_rydberg_probs, one_rydberg_probs, two_rydberg_probs


# get probabilities of 0, 1, and 2 atoms in Rydberg state for emulator
emu_zero_probs, emu_one_probs, emu_two_probs = generate_probabilities(emu_job)

# get probabilities of 0, 1, and 2 atoms in Rydberg state for HW
hw_zero_probs, hw_one_probs, hw_two_probs = generate_probabilities(hw_report)

# make three separate plots

# "00" density
gg_data = {
    "times": run_times,
    "emu_densities": emu_zero_probs,
    "hw_densities": emu_one_probs,
}
gg_source = ColumnDataSource(data=gg_data)

gg_density = figure(
    title="0 Rydberg",
    x_axis_label="Time (μs)",
    y_axis_label="Rydberg Density",
    tools="pan,wheel_zoom,box_zoom,reset,save",
    toolbar_location=None,
)

gg_density.axis.axis_label_text_font_size = "15pt"
gg_density.axis.major_label_text_font_size = "10pt"

emu_line = gg_density.line(
    x="times",
    y="emu_densities",
    source=gg_source,
    label="Emulator",
    color="grey",
    line_width=2,
)
gg_density.circle(x="times", y="emu_densities", source=gg_source, color="grey", size=8)
hw_line = gg_density.line(
    x="times",
    y="hw_densities",
    source=gg_source,
    label="Hardware",
    color="purple",
    line_width=2,
)
gg_density.circle(x="times", y="hw_densities", source=gg_source, color="purple", size=8)

hw_hover_tool = HoverTool(
    renderers=[hw_line],
    tooltips=[
        ("Backend", "Hardware"),
        ("Density", "@hw_densities"),
        ("Time", "@times μs"),
    ],
    mode="vline",
    attachment="right",
)
gg_density.add_tools(hw_hover_tool)
emu_hover_tool = HoverTool(
    renderers=[emu_line],
    tooltips=[
        ("Backend", "Emulator"),
        ("Density", "@emu_densities"),
        ("Time", "@times μs"),
    ],
    mode="vline",
    attachment="left",
)

gg_density.add_tools(emu_hover_tool)
cross_hair_tool = CrosshairTool(dimensions="height")
gg_density.add_tools(cross_hair_tool)

show(gg_density)


gr_rg_density = figure(
    title="1 Rydberg",
    x_axis_label="Time (us)",
    y_axis_label="Rydberg Density",
    tools="",
    toolbar_location=None,
)

gr_rg_density.axis.axis_label_text_font_size = "15pt"
gr_rg_density.axis.major_label_text_font_size = "10pt"

gr_rg_density.line(run_times, emu_one_probs, line_width=2, color="blue")


rr_density = figure(
    title="2 Rydberg",
    x_axis_label="Time (us)",
    y_axis_label="Rydberg Density",
    tools="",
    toolbar_location=None,
)

rr_density.axis.axis_label_text_font_size = "15pt"
rr_density.axis.major_label_text_font_size = "10pt"

rr_density.line(run_times, emu_two_probs, line_width=2, color="red")

p = row(gg_density, gr_rg_density, rr_density)

show(p)
