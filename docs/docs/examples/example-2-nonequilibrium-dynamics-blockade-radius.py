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
# # Whitepaper Example 2: Nonequilibrium Dynamics at Blockade Radius

# %%

from bloqade import start, cast
from bloqade.task import HardwareFuture

import numpy as np
import os

from bokeh.plotting import show, figure
from bokeh.io import output_notebook
from bokeh.models import HoverTool, CrosshairTool, ColumnDataSource

output_notebook()

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
hw_future.load_json(
    os.getcwd()
    + "/docs/docs/examples/"
    + "example-2-nonequilibrium-dynamics-blockade-radius-job.json"
)
hw_report = hw_future.report()


def get_rydberg_probs(report):
    bitstring_dicts = report.counts
    zero_rydberg_probs = []  # "00"
    one_rydberg_probs = []  # "01" or "10"
    two_rydberg_probs = []  # "11"

    for bitstring_dict in bitstring_dicts:
        successful_presort_shots = sum(bitstring_dict.values())
        zero_rydberg_probs.append(
            bitstring_dict.get("11", 0) / successful_presort_shots
        )
        one_rydberg_probs.append(
            (bitstring_dict.get("01", 0) + bitstring_dict.get("10", 0))
            / successful_presort_shots
        )
        two_rydberg_probs.append(bitstring_dict.get("00", 0) / successful_presort_shots)

    return zero_rydberg_probs, one_rydberg_probs, two_rydberg_probs


# get probabilities of 0, 1, and 2 atoms in Rydberg state for emulator
emu_zero_probs, emu_one_probs, emu_two_probs = get_rydberg_probs(emu_job)

# get probabilities of 0, 1, and 2 atoms in Rydberg state for HW
hw_zero_probs, hw_one_probs, hw_two_probs = get_rydberg_probs(hw_report)


# make three separate plots
def generate_plot(plt_title, source):
    plt = figure(
        title=plt_title,
        x_axis_label="Time (μs)",
        y_axis_label="Rydberg Density",
        tools="pan,wheel_zoom,box_zoom,reset,save",
        toolbar_location="right",
    )

    plt.axis.axis_label_text_font_size = "15pt"
    plt.axis.major_label_text_font_size = "10pt"

    source_keys = ["emu_densities", "hw_densities"]
    legend_labels = ["Emulator", "Hardware"]
    colors = ["grey", "purple"]
    hover_tool_attachments = ["left", "right"]
    for source_key, legend_label, color, hover_tool_attachment in zip(
        source_keys, legend_labels, colors, hover_tool_attachments
    ):
        line = plt.line(
            x="times",
            y=source_key,
            source=source,
            legend_label=legend_label,
            color=color,
        )

        plt.circle(x="times", y=source_key, source=source, color=color, size=8)

        plt.add_tools(
            HoverTool(
                renderers=[line],
                tooltips=[
                    ("Backend", legend_label),
                    ("Density", "@hw_densities"),
                    ("Time", "@times μs"),
                ],
                mode="vline",
                attachment=hover_tool_attachment,
            )
        )

    plt.add_tools(CrosshairTool(dimensions="height"))

    return plt


# %%
# gg density
gg_data = {
    "times": run_times,
    "emu_densities": emu_zero_probs,
    "hw_densities": hw_zero_probs,
}
gg_source = ColumnDataSource(data=gg_data)

show(generate_plot("0 Rydberg", gg_source))

# %%
# gr + rg density
gr_rg_data = {
    "times": run_times,
    "emu_densities": emu_one_probs,
    "hw_densities": hw_one_probs,
}
gr_rg_source = ColumnDataSource(data=gr_rg_data)

show(generate_plot("1 Rydberg", gr_rg_source))

# %%
rr_data = {
    "times": run_times,
    "emu_densities": emu_two_probs,
    "hw_densities": hw_two_probs,
}

rr_source = ColumnDataSource(data=rr_data)

show(generate_plot("2 Rydberg", rr_source))
