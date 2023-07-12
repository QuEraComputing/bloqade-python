from bloqade import start, var
from bloqade.task import HardwareFuture

import numpy as np
import os

from bokeh.models import ColumnDataSource, HoverTool
from bokeh.plotting import figure, show

delta = 0.377371  # Detuning
xi = 3.90242  # Phase jump
tau = 4.29268  # Time of each pulse

amplitude_max = 10
min_time_step = 0.05
detuning_value = delta * amplitude_max
T = tau / amplitude_max - min_time_step

durations = [
    min_time_step,
    T,
    min_time_step,
    min_time_step,
    min_time_step,
    T,
    min_time_step,
]
rabi_wf_values = [
    0.0,
    amplitude_max,
    amplitude_max,
    0.0,
    0.0,
    amplitude_max,
    amplitude_max,
    0.0,
]

t_run = var("t_run")

lp_gate_sequence = (
    start.rydberg.rabi.amplitude.uniform.piecewise_linear(durations, rabi_wf_values)
    .slice(0, t_run - min_time_step)
    .record("rabi_value")
    .linear("rabi_value", 0, min_time_step)
    .detuning.uniform.constant(detuning_value, sum(durations))
    .slice(0, t_run)
    .phase.uniform.piecewise_constant(durations, [0.0] * 4 + [xi] * 3)
    .slice(0, t_run)
    .sequence
)

run_times = np.arange(min_time_step, sum(durations), min_time_step)

# create a one atom and two atom example
atom_positions = [[(0, 0)], [(0, 0), (0, 4.0)]]
# file names for saving jobs
atom_positions_names = ["single_atom", "dual_atom"]

lp_gate_programs = []
for atom_position in atom_positions:
    lp_gate_programs.append(start.add_positions(atom_position).apply(lp_gate_sequence))

lp_gate_jobs = []
for lp_gate_program in lp_gate_programs:
    lp_gate_jobs.append(
        lp_gate_program.batch_assign(
            # not happy starting from t_run = 0.0, have to offset a little
            t_run=run_times
        )
    )

# submit to emulator
emu_jobs = []
for lp_gate_job in lp_gate_jobs:
    emu_jobs.append(lp_gate_job.braket_local_simulator(10000).submit().report())

# submit to HW

hw_jobs_json_dir = "./example-2-lp-gate-jobs/"
os.makedirs(hw_jobs_json_dir)
"""
for lp_gate_job, file_name in zip(lp_gate_jobs, atom_positions_names):
    (
        lp_gate_job.parallelize(24)
        .braket(100)
        .submit()
        .save_json(
            hw_jobs_json_dir + "/" + "example-2-lp-gate-" + file_name + "-job.json"
        )
    )
"""

# load results from HW
single_atom_hw_future = HardwareFuture()
single_atom_hw_future.load_json(
    hw_jobs_json_dir + "example-2-lp-gate-" + atom_positions_names[0] + "-job.json"
)
dual_atom_hw_future = HardwareFuture()
dual_atom_hw_future.load_json(
    hw_jobs_json_dir + "example-2-lp-gate-" + atom_positions_names[1] + "-job.json"
)

hw_jobs = [single_atom_hw_future.report(), dual_atom_hw_future.report()]


def generate_plots(title, source):
    plt = figure(
        title=title, x_axis_label="Time (μs)", y_axis_label="Rydberg Density", tools=""
    )

    backends = ["Emulator", "Hardware"]
    src_keys = ["emu_densities", "hw_densities"]
    colors = ["grey", "purple"]
    hover_tool_attachment = ["left", "right"]

    for backend, src_key, color in zip(backends, src_keys, colors):
        line = plt.line(
            x="times",
            y=src_key,
            source=source,
            legend_label=backend,
        )
        plt.circle(
            x="times",
            y=src_key,
            source=source,
            color=color,
            size=8,
        )
        plt.add_tools(
            HoverTool(
                renders=[line],
                tooltips=[
                    ("Backend", backend),
                    ("Density", "@" + src_key),
                    ("Time", "@times μs"),
                ],
                mode="vline",
                attachment=hover_tool_attachment,
            )
        )

    return plt


## Single Atom data source
single_atom_src = ColumnDataSource(
    data={
        "times": run_times,
        "emu_densities": emu_jobs[0].rydberg_densities(),
        "hw_densities": hw_jobs[0].rydberg_densities(),
    }
)

## Dual Atom data source
dual_atom_src = ColumnDataSource(
    data={
        "times": run_times,
        "emu_densities": emu_jobs[1].rydberg_densities(),
        "hw_densities": hw_jobs[1].rydberg_densities(),
    }
)

show(generate_plots("Single Atom LP Gate", single_atom_src))

show(generate_plots("Dual Atom LP Gate", dual_atom_src))
