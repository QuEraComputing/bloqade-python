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
# # Ramsey Protocol
# ## Introduction
# In this example we show how to use Bloqade to emulate a
# Ramsey protocol as well as run it on hardware.

# %%
from bloqade import start
from bloqade.task import HardwareBatchResult

import os

import numpy as np
from bokeh.io import output_notebook
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource, HoverTool, CrosshairTool

output_notebook()

# %% [markdown]

# define program with one atom, with constant detuning but variable Rabi frequency,
# where an initial pi/2 pulse is applied, followed by some time gap and a -pi/2 pulse

# %%
plateau_time = (np.pi / 2 - 0.625) / 12.5
wf_durations = [0.05, plateau_time, 0.05, "t_run", 0.05, plateau_time, 0.05]
rabi_wf_values = [0.0, 12.5, 12.5, 0.0] * 2  # repeat values twice

ramsey_program = (
    start.add_position([0, 0])
    .rydberg.rabi.amplitude.uniform.piecewise_linear(wf_durations, rabi_wf_values)
    .detuning.uniform.piecewise_linear(wf_durations, [10.5] * (len(wf_durations) + 1))
)

# %% [markdown]
# Assign values to the variables in the program,
# allowing `t_run` (time gap between the two pi/2 pulses)
# to sweep across a range of values.

# %%
ramsey_job = ramsey_program.batch_assign(t_run=np.around(np.arange(0, 30, 1) * 0.1, 13))

# %% [markdown]
# Run the program in emulation, obtaining a report
# object. For each possible set of variable values
# to simulate (in this case, centered around the
# `t_run` variable), let the task have 10000 shots.

# %%
emu_job = ramsey_job.braket_local_simulator(10000).submit().report()

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
    ramsey_job.parallelize(24)
    .braket(100)
    .submit()
    .save_json("ramsey-job.json")
)
"""
# %% [markdown]
# Load JSON and pull results from Braket

# %%
hw_future = HardwareBatchResult.load_json(
    os.getcwd() + "/docs/docs/examples/" + "ramsey-job.json"
)
hw_rydberg_densities = hw_future.report().rydberg_densities()

# %% [markdown]
# We can now plot the results from the hardware and emulation together.

# %%
data = {
    "times": np.around(np.arange(0, 30, 1) * 0.1, 13),
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
