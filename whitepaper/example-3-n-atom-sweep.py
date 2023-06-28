# range(5,14,2) goes from 5 to 13 in steps of 2 for n_atoms

from bloqade import start
from bloqade.ir.location import Chain

from bokeh.plotting import figure, show

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

for n_atoms in range(5, 14, 2):
    n_atom_programs.append(
        Chain(n_atoms, 6.1).apply(sweep_sequence).assign(sweep_time=2.4)
    )

# run on emulator
n_atom_reports = []

for program in n_atom_programs:
    n_atom_reports.append(program.braket_local_simulator(10000).submit().report())


# needs to be inverted
def gen_z2_str_sequence(seq_len):
    seq = "0"
    for _ in range(seq_len - 1):
        if seq[-1] == "0":
            seq += "1"
        else:
            seq += "0"
    return seq


z2_probabilities = []

for n_atom_report, n_atoms in zip(n_atom_reports, range(5, 14, 2)):
    z2_probabilities.append(
        n_atom_report.counts[0][gen_z2_str_sequence(n_atoms)]
        / sum(list(n_atom_report.counts[0].values()))
    )

# Plot results

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
