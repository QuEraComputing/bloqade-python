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
# # Single Qubit Rabi Oscillations
# ## Introduction
# In this example we show how to use Bloqade to emulate a
# Rabi oscillation as well as run it on hardware.

# %%
from bloqade import start, cast
from bloqade.task import HardwareFuture

import os
import numpy as np

from bokeh.io import output_notebook
from bokeh.plotting import figure, show
from bokeh.models import HoverTool, ColumnDataSource, CrosshairTool

output_notebook()

# %% [markdown]

# define program with one atom, with constant detuning but variable Rabi frequency,
# ramping up to "rabi_value" and then returning to 0.0.

# %%
durations = cast(["ramp_time", "run_time", "ramp_time"])

rabi_oscillations_program = (
    start.add_position((0, 0))
    .rydberg.rabi.amplitude.uniform.piecewise_linear(
        durations=durations, values=[0, "rabi_value", "rabi_value", 0]
    )
    .detuning.uniform.constant(duration=sum(durations), value=0)
)

# %% [markdown]
# Assign values to the variables in the program,
# allowing the `run_time` (time the Rabi amplitude stays at the value of
# "rabi_frequency" ) to sweep across a range of values.

# %%
rabi_oscillation_job = rabi_oscillations_program.assign(
    ramp_time=0.06, rabi_value=15, detuning_value=0.0
).batch_assign(run_time=np.around(np.arange(0, 21, 1) * 0.05, 13))

# %% [markdown]
# Run the program in emulation, obtaining a report
# object. For each possible set of variable values
# to simulate (in this case, centered around the
# `run_time` variable), let the task have 10000 shots.

# %%
emu_report = rabi_oscillation_job.braket_local_simulator(10000).submit().report()

# %% [markdown]
# Submit the same program to hardware,
# this time using `.parallelize` to make a copy of the original geometry
# (a single atom) that fills the FOV (Field-of-View Space), with at least
# 24 micrometers of distance between each atom.
#
# Unlike the emulation above, we only let each task
# run with 100 shots. A collection of tasks is known as a
# "Job" in Bloqade and jobs can be saved in JSON format
# so you can reload them later (a necessity considering
# how long it may take for the machine to handle tasks in the queue)

# %%
"""
(
    rabi_oscillation_job.parallelize(24)
    .braket(100)
    .submit()
    .save_json("rabi-job.json")
)
"""

# %% [markdown]
# Load JSON and pull results from Braket

# %%
hw_future = HardwareFuture()
hw_future.load_json(os.getcwd() + "/docs/docs/examples/" + "rabi-job.json")
hw_rydberg_densities = hw_future.report().rydberg_densities()

# %% [markdown]
# We can now plot the results from the hardware and emulation together.

# %%
data = {
    "times": np.around(np.arange(0, 21, 1) * 0.05, 13),
    "emu_densities": emu_report.rydberg_densities()[0].to_list(),
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
