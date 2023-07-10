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

# gg density
gg_data = {
    "times": run_times,
    "emu_densities": emu_zero_probs,
    "hw_densities": hw_zero_probs,
}
gg_source = ColumnDataSource(data=gg_data)

gg_plt = figure(
    title="0 Rydberg",
    x_axis_label="Time (μs)",
    y_axis_label="Rydberg Density",
    tools="pan,wheel_zoom,box_zoom,reset,save",
    toolbar_location=None,
)

gg_plt.axis.axis_label_text_font_size = "15pt"
gg_plt.axis.major_label_text_font_size = "10pt"

gg_emu_line = gg_plt.line(
    x="times",
    y="emu_densities",
    source=gg_source,
    label="Emulator",
    color="grey",
    line_width=2,
)
gg_plt.circle(x="times", y="emu_densities", source=gg_source, color="grey", size=8)
gg_hw_line = gg_plt.line(
    x="times",
    y="hw_densities",
    source=gg_source,
    label="Hardware",
    color="purple",
    line_width=2,
)
gg_plt.circle(x="times", y="hw_densities", source=gg_source, color="purple", size=8)

gg_hw_hover_tool = HoverTool(
    renderers=[gg_hw_line],
    tooltips=[
        ("Backend", "Hardware"),
        ("Density", "@hw_densities"),
        ("Time", "@times μs"),
    ],
    mode="vline",
    attachment="right",
)
gg_plt.add_tools(gg_hw_hover_tool)
gg_emu_hover_tool = HoverTool(
    renderers=[gg_emu_line],
    tooltips=[
        ("Backend", "Emulator"),
        ("Density", "@emu_densities"),
        ("Time", "@times μs"),
    ],
    mode="vline",
    attachment="left",
)

gg_plt.add_tools(gg_emu_hover_tool)
gg_cross_hair_tool = CrosshairTool(dimensions="height")
gg_plt.add_tools(gg_cross_hair_tool)

# show(gg_plt)

# gr + rg density
gr_rg_data = {
    "times": run_times,
    "emu_densities": emu_one_probs,
    "hw_densities": hw_one_probs,
}
gr_rg_source = ColumnDataSource(data=gr_rg_data)

gr_rg_plt = figure(
    title="1 Rydberg",
    x_axis_label="Time (μs)",
    y_axis_label="Rydberg Density",
    tools="pan,wheel_zoom,box_zoom,reset,save",
    toolbar_location=None,
)

gr_rg_plt.axis.axis_label_text_font_size = "15pt"
gr_rg_plt.axis.major_label_text_font_size = "10pt"

gr_rg_emu_line = gr_rg_plt.line(
    x="times",
    y="emu_densities",
    source=gr_rg_source,
    label="Emulator",
    color="grey",
    line_width=2,
)
gr_rg_plt.circle(x="times", y="emu_densities", source=gr_rg_source, color="grey", size=8)
gr_rg_hw_line = gr_rg_plt.line(
    x="times",
    y="hw_densities",
    source=gr_rg_source,
    label="Hardware",
    color="purple",
    line_width=2,
)
gr_rg_plt.circle(x="times", y="hw_densities", source=gr_rg_source, color="purple", size=8)

gr_rg_hw_hover_tool = HoverTool(
    renderers=[gr_rg_hw_line],
    tooltips=[
        ("Backend", "Hardware"),
        ("Density", "@hw_densities"),
        ("Time", "@times μs"),
    ],
    mode="vline",
    attachment="right",
)
gr_rg_plt.add_tools(gr_rg_hw_hover_tool)
gr_rg_emu_hover_tool = HoverTool(
    renderers=[gr_rg_emu_line],
    tooltips=[
        ("Backend", "Emulator"),
        ("Density", "@emu_densities"),
        ("Time", "@times μs"),
    ],
    mode="vline",
    attachment="left",
)

gr_rg_plt.add_tools(gr_rg_emu_hover_tool)
gr_rg_cross_hair_tool = CrosshairTool(dimensions="height")
gr_rg_plt.add_tools(gr_rg_cross_hair_tool)

# show(gr_rg_plt)

## plot rr density
rr_data = {
    "times": run_times,
    "emu_densities": emu_one_probs,
    "hw_densities": hw_one_probs,
}
rr_source = ColumnDataSource(data=rr_data)

rr_plt = figure(
    title="2 Rydberg",
    x_axis_label="Time (μs)",
    y_axis_label="Rydberg Density",
    tools="pan,wheel_zoom,box_zoom,reset,save",
    toolbar_location=None,
)

rr_plt.axis.axis_label_text_font_size = "15pt"
rr_plt.axis.major_label_text_font_size = "10pt"

rr_emu_line = rr_plt.line(
    x="times",
    y="emu_densities",
    source=rr_source,
    label="Emulator",
    color="grey",
    line_width=2,
)
rr_plt.circle(x="times", y="emu_densities", source=rr_source, color="grey", size=8)
rr_hw_line = rr_plt.line(
    x="times",
    y="hw_densities",
    source=rr_source,
    label="Hardware",
    color="purple",
    line_width=2,
)
rr_plt.circle(x="times", y="hw_densities", source=rr_source, color="purple", size=8)

rr_hw_hover_tool = HoverTool(
    renderers=[rr_hw_line],
    tooltips=[
        ("Backend", "Hardware"),
        ("Density", "@hw_densities"),
        ("Time", "@times μs"),
    ],
    mode="vline",
    attachment="right",
)
rr_plt.add_tools(rr_hw_hover_tool)
rr_emu_hover_tool = HoverTool(
    renderers=[rr_emu_line],
    tooltips=[
        ("Backend", "Emulator"),
        ("Density", "@emu_densities"),
        ("Time", "@times μs"),
    ],
    mode="vline",
    attachment="left",
)

rr_plt.add_tools(rr_emu_hover_tool)
rr_cross_hair_tool = CrosshairTool(dimensions="height")
rr_plt.add_tools(rr_cross_hair_tool)

# show(rr_plt)

p = row(gg_plt, gr_rg_plt, rr_plt)

show(p)
