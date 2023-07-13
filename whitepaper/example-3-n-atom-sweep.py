# range(5,14,2) goes from 5 to 13 in steps of 2 for n_atoms

from bloqade import start
from bloqade.ir.location import Chain
from bloqade.task import HardwareFuture

import os
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource, HoverTool, CrosshairTool

rabi_amplitude_values = [0.0, 15.8, 15.8, 0.0]
rabi_detuning_values = [-16.33, -16.33, 16.33, 16.33]
durations = [0.8, "sweep_time", 0.8]

sweep_sequence = (
    start.rydberg.rabi.amplitude.uniform.piecewise_linear(
        durations, rabi_amplitude_values
    )
    .detuning.uniform.piecewise_linear(durations, rabi_detuning_values)
    .sequence
)

n_atom_programs = []

lattice_const = 6.1

for n_atoms in range(5, 14, 2):
    n_atom_programs.append(
        Chain(n_atoms, lattice_const).apply(sweep_sequence).assign(sweep_time=2.4)
    )

# run on emulator
emu_jobs = []

for program in n_atom_programs:
    emu_jobs.append(program.braket_local_simulator(10000).submit().report())

# make a folder to store results
hw_jobs_json_dir = "./example-3-n-atom-sweep-jobs"


os.makedirs(hw_jobs_json_dir)
"""
for program, n_atoms in zip(n_atom_programs, range(5, 14, 2)):
    (
        program.parallelize(3 * lattice_const)
        .braket(100)
        .submit()
        .save_json(hw_jobs_json_dir + "/" + str(n_atoms) + ".json")
    )
"""
# retrieve results from HW
hw_jobs = [HardwareFuture() for _ in range(5, 14, 2)]
for i, n_atoms in enumerate(range(5, 14, 2)):
    hw_jobs[i].load_json(hw_jobs_json_dir + "/" + str(n_atoms) + ".json")


# needs to be inverted
def gen_z2_str_sequence(seq_len):
    seq = "0"
    for _ in range(seq_len - 1):
        if seq[-1] == "0":
            seq += "1"
        else:
            seq += "0"
    return seq


# get Z2 probabilities on emulator
emu_z2_probabilities = []

for emu_job, n_atoms in zip(emu_jobs, range(5, 14, 2)):
    emu_z2_probabilities.append(
        emu_job.counts[0][gen_z2_str_sequence(n_atoms)]
        / sum(list(emu_job.counts[0].values()))
    )

# get Z2 probabilities on HW
hw_z2_probabilities = []

for hw_job, n_atoms in zip(hw_jobs, range(5, 14, 2)):
    hw_z2_probabilities.append(
        hw_job.report().counts[0].get(gen_z2_str_sequence(n_atoms), 0)
        / sum(hw_job.report().counts[0].values())
    )

z2_probability_plt = figure(
    x_axis_label="Number of sites",
    y_axis_label="Z_2 state probability",
    toolbar_location="right",
    tools="save",
)

z2_probability_plt.axis.axis_label_text_font_size = "15pt"
z2_probability_plt.axis.major_label_text_font_size = "10pt"

source = ColumnDataSource(
    data={
        "n_atoms": list(range(5, 14, 2)),
        "emu_z2_probabilities": emu_z2_probabilities,
        "hw_z2_probabilities": hw_z2_probabilities,
    }
)

legend_labels = ["Emulator", "Hardware"]
source_keys = ["emu_z2_probabilities", "hw_z2_probabilities"]
colors = ["grey", "purple"]

for legend_label, source_key, color in zip(legend_labels, source_keys, colors):
    line = z2_probability_plt.line(
        x="n_atoms",
        y=source_key,
        source=source,
        legend_label=legend_label,
        line_width=2,
        color=color,
    )
    z2_probability_plt.circle(
        x="n_atoms", y=source_key, source=source, color=color, size=8
    )
    z2_probability_plt.add_tools(
        HoverTool(
            renderers=[line],
            tooltips=[
                ("Backend", legend_label),
                ("Number of sites", "@n_atoms"),
                ("Z_2 state probability", "@" + source_key),
            ],
            mode="vline",
        )
    )

z2_probability_plt.add_tools(CrosshairTool(dimensions="height"))


show(z2_probability_plt)


# Plot results
"""
p = figure(
    x_axis_label="Number of sites",
    y_axis_label="Z_2 state probability",
    toolbar_location=None,
    tools="",
)
p.axis.axis_label_text_font_size = "15pt"
p.axis.major_label_text_font_size = "10pt"


p.line(list(range(5, 14, 2)), z2_probabilities, line_width=2)
p.cross(list(range(5, 14, 2)), z2_probabilities, size=25, fill_color="black")

show(p)
"""
