# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     hide_notebook_metadata: false
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.14.5
#   kernelspec:
#     display_name: .venv
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Whitepaper Example 1C: Floquet Protocol

# %%
from bloqade import start, cast
from bloqade.task import HardwareFuture

import numpy as np
import os

from bokeh.io import output_notebook
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource, HoverTool, CrosshairTool

output_notebook()

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
"""
(
    floquet_job.parallelize(24).braket(50).submit().save_json("example-1c-floquet-job.json")
)
"""

hw_future = HardwareFuture()
hw_future.load_json(
    os.getcwd() + "/docs/docs/examples/" + "example-1c-floquet-job.json"
)
hw_rydberg_densities = hw_future.report().rydberg_densities()

# plot results
data = {
    "times": np.around(np.linspace(min_time_step, 3, 101), 13),
    "emu_densities": emu_job.rydberg_densities()[0].to_list(),
    "hw_densities": hw_rydberg_densities[0].to_list(),
}
source = ColumnDataSource(data=data)

p = figure(
    x_axis_label="Time (μs)",
    y_axis_label="Rydberg Density",
    toolbar_location="right",
    tools=["pan,wheel_zoom,box_zoom,reset,save"],
)

p.axis.axis_label_text_font_size = "15pt"
p.axis.major_label_text_font_size = "10pt"

# emulator densities
emu_line = p.line(
    x="times",
    y="emu_densities",
    source=source,
    legend_label="Emulator",
    color="grey",
    line_width=2,
)
p.circle(x="times", y="emu_densities", source=source, color="grey", size=8)
# hardware densities
hw_line = p.line(
    x="times",
    y="hw_densities",
    source=source,
    legend_label="Hardware",
    color="purple",
    line_width=2,
)
p.circle(x="times", y="hw_densities", source=source, color="purple", size=8)

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
p.add_tools(hw_hover_tool)
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
p.add_tools(emu_hover_tool)
cross_hair_tool = CrosshairTool(dimensions="height")
p.add_tools(cross_hair_tool)

show(p)
