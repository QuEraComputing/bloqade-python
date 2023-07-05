from bloqade import start

import numpy as np
from bokeh.plotting import figure, show

durations = [1, 2, 1]

two_qubit_adiabatic_program = (
    start.add_positions([(0, 0), (0, "distance")])
    .rydberg.rabi.amplitude.uniform.piecewise_linear(durations, [0, 15, 15, 0])
    .detuning.uniform.piecewise_linear(durations, [-15, -15, 15, 15])
)


two_qubit_adiabatic_job = two_qubit_adiabatic_program.batch_assign(
    distance=np.around(np.arange(4, 11, 1), 13)
)

n_shots = 10000

emu_job = two_qubit_adiabatic_job.braket_local_simulator(n_shots).submit().report()

hw_job = (
    two_qubit_adiabatic_job.parallelize(24)
    .braket(100)
    .submit()
    .save_json("example-2-two-qubit-adiabatic-job.json")
)

# want to plot the 0 rydberg probability,
# 1 rydberg probability,
# and 2 rydberg probabilities

bitstring_dicts = emu_job.counts
zero_rydberg_probs = []  # "00"
one_rydberg_probs = []  # "01" or "10"
two_rydberg_probs = []  # "11"

for bitstring_dict in bitstring_dicts:
    zero_rydberg_probs.append(bitstring_dict.get("11", 0) / n_shots)
    one_rydberg_probs.append(
        (bitstring_dict.get("01", 0) + bitstring_dict.get("10", 0)) / n_shots
    )
    two_rydberg_probs.append(bitstring_dict.get("00", 0) / n_shots)

# plot the results
p = figure(
    x_axis_label="Distance (um)",
    y_axis_label="Probability",
    tools="",
    toolbar_location=None,
)

p.axis.axis_label_text_font_size = "15pt"
p.axis.major_label_text_font_size = "10pt"

p.line(
    np.arange(4, 11, 1),
    zero_rydberg_probs,
    legend_label="0 Rydberg",
    line_color="green",
    line_width=2,
)
p.line(
    np.arange(4, 11, 1),
    one_rydberg_probs,
    legend_label="1 Rydberg",
    line_color="yellow",
    line_width=2,
)
p.line(
    np.arange(4, 11, 1),
    two_rydberg_probs,
    legend_label="2 Rydberg",
    line_color="red",
    line_width=2,
)

show(p)
