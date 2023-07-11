from bloqade import start
from bloqade.task import HardwareFuture

import numpy as np
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource, CrosshairTool, HoverTool

durations = [1, 2, 1]

two_qubit_adiabatic_program = (
    start.add_positions([(0, 0), (0, "distance")])
    .rydberg.rabi.amplitude.uniform.piecewise_linear(durations, [0, 15, 15, 0])
    .detuning.uniform.piecewise_linear(durations, [-15, -15, 15, 15])
)


two_qubit_adiabatic_job = two_qubit_adiabatic_program.batch_assign(
    distance=np.around(np.arange(4, 11, 1), 13)
)

# submit to local emulator
emu_job = two_qubit_adiabatic_job.braket_local_simulator(10000).submit().report()

# submit to HW
"""
(
    two_qubit_adiabatic_job.parallelize(24)
    .braket(100)
    .submit()
    .save_json("example-2-two-qubit-adiabatic-job.json")
)
"""

# retrieve data from HW
hw_future = HardwareFuture()
hw_future.load_json("example-2-two-qubit-adiabatic-job.json")
hw_report = hw_future.report()

# want to plot the 0 rydberg probability,
# 1 rydberg probability,
# and 2 rydberg probabilities


def get_rydberg_probs(report):
    bitstring_dicts = report.counts
    zero_rydberg_probs = []  # "00"
    one_rydberg_probs = []  # "01" or "10"
    two_rydberg_probs = []  # "11"

    for bitstring_dict in bitstring_dicts:
        successful_presort_shots = sum(bitstring_dict.values())
        zero_rydberg_probs.append(
            bitstring_dict.get("11", 0) / successful_presort_shots
        )  # n_shots needs to be dynamically calculated
        one_rydberg_probs.append(
            (bitstring_dict.get("01", 0) + bitstring_dict.get("10", 0))
            / successful_presort_shots
        )
        two_rydberg_probs.append(bitstring_dict.get("00", 0) / successful_presort_shots)

    return zero_rydberg_probs, one_rydberg_probs, two_rydberg_probs


# format data properly
emu_data = {
    "distance": [np.around(np.arange(4, 11, 1), 13)] * 3,
    "probs": [*get_rydberg_probs(emu_job)],
}
emu_source = ColumnDataSource(data=emu_data)

hw_zero_rydberg_probs, hw_one_rydberg_probs, hw_two_rydberg_probs = get_rydberg_probs(
    hw_report
)
hw_data = {
    "distance": np.around(np.arange(4, 11, 1), 13),
    "gg_probs": hw_zero_rydberg_probs,
    "gr_rg_probs": hw_one_rydberg_probs,
    "rr_probs": hw_two_rydberg_probs,
}
hw_source = ColumnDataSource(data=hw_data)

# plot the results
rydberg_probs_plt = figure(
    x_axis_label="Distance (μm)",
    y_axis_label="Probability",
    toolbar_location="right",
    tools=["pan,wheel_zoom,box_zoom,reset,save"],
)

rydberg_probs_plt.axis.axis_label_text_font_size = "15pt"
rydberg_probs_plt.axis.major_label_text_font_size = "10pt"

# multiline for emulator
rydberg_probs_plt.multi_line(
    xs="distance",
    ys="probs",
    source=emu_source,
    line_width=2,
    color="grey",
    legend_label="Emulator",
)

# combination of markers and lines for other plots
# zero rydberg atom case
hw_data_keys = ["gg_probs", "gr_rg_probs", "rr_probs"]
legend_labels = ["0 Rydberg", "1 Rydberg", "2 Rydberg"]
line_colors = ["green", "yellow", "red"]

hw_lines = []
for data_key, legend_label, line_color in zip(hw_data_keys, legend_labels, line_colors):
    hw_lines.append(
        rydberg_probs_plt.line(
            x="distance",
            y=data_key,
            source=hw_source,
            legend_label=legend_label,
            color=line_color,
            line_width=2,
        )
    )

    rydberg_probs_plt.circle(
        x="distance", y=data_key, source=hw_source, color=line_color, size=8
    )

# add hover tools
for hw_line, legend_label, hw_data_key in zip(hw_lines, legend_labels, hw_data_keys):
    rydberg_probs_plt.add_tools(
        HoverTool(
            renderers=[hw_line],
            tooltips=[
                ("Probability of", legend_label),
                ("Distance", "@distance μm"),
                ("Probability", "@" + hw_data_key),
            ],
            mode="vline",
        )
    )

cross_hair_tool = CrosshairTool(dimensions="height")
rydberg_probs_plt.add_tools(cross_hair_tool)

show(rydberg_probs_plt)
