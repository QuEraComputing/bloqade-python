# %% [markdown]
# # Multi-qubit Blockaded Rabi Oscillations
#
# In this example we show how rabi oscillations behave when multiple
# Rydberg atoms blockade eachother

# %%
from bloqade import start, cast
from bloqade.task import HardwareBatchResult

import numpy as np
import os

from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource, HoverTool, CrosshairTool

# %% [markdown]
# We define a function below to allow multiple programs to be defined with varying
# numbers of atoms as well as initial geometries, all of which have the
# atoms blockade eachother.
#
# For this example we choose to use 7 atoms in a hexagonal geometry, with
# the last atom at the center.
#
# The waveforms are the same as the two-qubit adiabatic sweep example you saw earlier,
# but we sweep over the total run time of the rabi pulse
# (ignoring the ramp up and ramp down times) versus the distance between atoms.

# %%


def program_init(num_atoms):
    distance = 4
    inv_sqrt_2_rounded = 2.6

    if num_atoms == 1:
        new_program = start.add_position((0, 0))
    elif num_atoms == 2:
        new_program = start.add_positions([(0, 0), (0, distance)])
    elif num_atoms == 3:
        new_program = start.add_positions(
            [(-inv_sqrt_2_rounded, 0), (inv_sqrt_2_rounded, 0), (0, distance)]
        )
    elif num_atoms == 4:
        new_program = start.add_positions(
            [(0, 0), (distance, 0), (0, distance), (distance, distance)]
        )
    elif num_atoms == 7:
        new_program = start.add_positions(
            [
                (0, 0),
                (distance, 0),
                (-0.5 * distance, distance),
                (0.5 * distance, distance),
                (1.5 * distance, distance),
                (0, 2 * distance),
                (distance, 2 * distance),
            ]
        )
    else:
        raise ValueError("natoms must be 1, 2, 3, 4, or 7")

    return new_program


# whitepaper example defaults to 7 qubits,
# can become quite slow trying to get results on laptop
program = program_init(7)

durations = cast(["ramp_time", "t_run", "ramp_time"])

multi_qubit_blockade_program = program.rydberg.rabi.amplitude.uniform.piecewise_linear(
    durations, [0, 5, 5, 0]
).detuning.uniform.constant(value=0, duration=sum(durations))


multi_qubit_blockade_job = multi_qubit_blockade_program.batch_assign(
    t_run=0.05 * np.arange(21)
).assign(ramp_time=0.06)

# %% [markdown]
# We now run the program on the local emulator as well as hardware

# %%

# run on local emulator
emu_job = multi_qubit_blockade_job.braket_local_simulator(10000).submit().report()

# run on hardware
"""
(
    multi_qubit_blockade_job.parallelize(24)
    .braket(100)
    .submit()
    .save_json("example-2-multi-qubit-blockaded-job.json")
)
"""

# %% [markdown]
# We retrieve results from the hardware

# load results from HW

# %%
hw_future = HardwareBatchResult.load_json(
    os.getcwd() + "/docs/docs/examples/" + "multi-qubit-blockaded-rabi-job.json"
)
hw_densities = hw_future.report().rydberg_densities()

# %% [markdown]
# Now we plot the results

# %%

# Put data into format that Bokeh can consume,
# want to take the mean across all the densities
data = {
    "times": 0.05 * np.arange(21),
    "emu_mean_densities": emu_job.rydberg_densities().mean(axis=1),
    "hw_mean_densities": hw_densities.mean(axis=1),
}
source = ColumnDataSource(data=data)

# plot results
mean_densities_plt = figure(
    x_axis_label="Time (us)",
    y_axis_label="Mean Rydberg Density",
    tools="",
    toolbar_location=None,
)

mean_densities_plt.axis.axis_label_text_font_size = "15pt"
mean_densities_plt.axis.major_label_text_font_size = "10pt"

# plot emulator data
emu_line = mean_densities_plt.line(
    x="times",
    y="emu_mean_densities",
    source=source,
    legend_label="Emulator",
    color="grey",
    line_width=2,
)
mean_densities_plt.circle(
    x="times", y="emu_mean_densities", source=source, color="grey", size=8
)

# hardware densities
hw_line = mean_densities_plt.line(
    x="times",
    y="hw_mean_densities",
    source=source,
    legend_label="Hardware",
    color="purple",
    line_width=2,
)
mean_densities_plt.circle(
    x="times", y="hw_mean_densities", source=source, color="purple", size=8
)

# add hover tools and interactive goodies
hw_hover_tool = HoverTool(
    renderers=[hw_line],
    tooltips=[
        ("Backend", "Hardware"),
        ("Mean Density", "@hw_mean_densities"),
        ("Time", "@times μs"),
    ],
    mode="vline",
    attachment="right",
)
mean_densities_plt.add_tools(hw_hover_tool)
emu_hover_tool = HoverTool(
    renderers=[emu_line],
    tooltips=[
        ("Backend", "Emulator"),
        ("Mean Density", "@emu_mean_densities"),
        ("Time", "@times μs"),
    ],
    mode="vline",
    attachment="left",
)
mean_densities_plt.add_tools(emu_hover_tool)
cross_hair_tool = CrosshairTool(dimensions="height")
mean_densities_plt.add_tools(cross_hair_tool)

show(mean_densities_plt)
