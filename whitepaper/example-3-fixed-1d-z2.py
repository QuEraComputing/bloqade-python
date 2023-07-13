from bloqade.ir.location import Chain
from bloqade.task import HardwareFuture

from bokeh.models import (
    ColumnDataSource,
    HoverTool,
    CrosshairTool,
    LinearColorMapper,
    ColorBar,
    BasicTicker,
    Range1d,
)
from bokeh.plotting import figure, show
import numpy as np

n_atoms = 11
lattice_const = 6.1

rabi_amplitude_values = [0.0, 15.8, 15.8, 0.0]
rabi_detuning_values = [-16.33, -16.33, 16.33, 16.33]
durations = [0.8, "sweep_time", 0.8]

fixed_1d_z2_prog = (
    Chain(n_atoms, lattice_const)
    .rydberg.rabi.amplitude.uniform.piecewise_linear(durations, rabi_amplitude_values)
    .detuning.uniform.piecewise_linear(durations, rabi_detuning_values)
)

fixed_1d_z2_job = fixed_1d_z2_prog.assign(sweep_time=2.4)

# submit to emulator
emu_job = fixed_1d_z2_job.braket_local_simulator(10000).submit().report()

# submit to HW
"""
(
    fixed_1d_z2_job.parallelize(3 * lattice_const)
    .braket(100)
    .submit()
    .save_json("example-3-fixed-1d-z2-job.json")
)
"""

# retrieve results from HW
hw_future = HardwareFuture()
hw_future.load_json("example-3-fixed-1d-z2-job.json")
hw_job = hw_future.report()


def generate_density_bar_plots(report, title, color):
    source = ColumnDataSource(
        data={
            "atom_indices": list(range(n_atoms)),
            "densities": report.rydberg_densities().iloc[0],
        }
    )

    plt = figure(
        title=title,
        x_axis_label="Site Index",
        y_axis_label="Rydberg Density",
        toolbar_location="right",
        tools="save",
        y_range=Range1d(0, 1),
    )

    plt.title.text_font_size = "20pt"
    plt.axis.axis_label_text_font_size = "15pt"
    plt.axis.major_label_text_font_size = "10pt"

    plt.vbar(
        x="atom_indices",
        top="densities",
        source=source,
        color=color,
    )

    plt.add_tools(
        HoverTool(
            tooltips=[("Site Index", "@atom_indices"), ("Density", "@densities")],
            mode="vline",
        )
    )
    plt.add_tools(CrosshairTool(dimensions="height"))

    return plt


## Plots

# plot simulated densities bar plot
show(generate_density_bar_plots(emu_job, "Simulated Densities", "gray"))

# plot HW densities bar plot
show(generate_density_bar_plots(hw_job, "Actual Densities", "purple"))


def get_n_most_probable_states(report, top_n):
    state_counts = report.counts[0]
    total_shots = sum(state_counts.values())
    state_probabilities = {
        state: counts / total_shots for state, counts in state_counts.items()
    }
    sorted_state_probabilities = sorted(
        state_probabilities.items(), key=lambda item: item[1], reverse=True
    )

    top_n_states = []
    top_n_probabilities = []
    for i in range(top_n):
        state, probability = sorted_state_probabilities[i]
        top_n_states.append(state)
        top_n_probabilities.append(probability)

    return top_n_states, top_n_probabilities


def generate_probability_bar_plots(report, title, color):
    top_n_states, top_n_probabilities = get_n_most_probable_states(report, 7)

    source = ColumnDataSource(
        data={"states": top_n_states, "probabilities": top_n_probabilities}
    )

    plt = figure(
        title=title,
        x_axis_label="Measured State",
        y_axis_label="Probability",
        toolbar_location="right",
        tools="save",
        x_range=top_n_states,
        y_range=Range1d(0, 1),
    )

    plt.title.text_font_size = "20pt"
    plt.axis.axis_label_text_font_size = "15pt"
    plt.axis.major_label_text_font_size = "10pt"

    plt.vbar(x="states", top="probabilities", source=source, color=color, width=0.8)

    plt.xaxis.major_tick_in = 5
    plt.xaxis.major_tick_out = 0
    plt.xaxis.major_label_orientation = np.pi / 4

    plt.add_tools(
        HoverTool(
            tooltips=[("State", "@states"), ("Probability", "@probabilities")],
            mode="vline",
        )
    )

    plt.add_tools(CrosshairTool(dimensions="height"))

    return plt


show(generate_probability_bar_plots(emu_job, "Simulated Probabilities", "gray"))

show(generate_probability_bar_plots(hw_job, "Actual Probabilities", "purple"))


# correlation plot
def calculate_correlation(report, n_atoms):
    correlation_table = np.zeros((n_atoms, n_atoms))

    for i in range(n_atoms):
        for j in range(n_atoms):
            correlation_table[i, j] = (
                (1 - report.dataframe.iloc[:, i]) * (1 - report.dataframe.iloc[:, j])
            ).mean() - report.rydberg_densities().iloc[
                0, i
            ] * report.rydberg_densities().iloc[
                0, j
            ]

    return correlation_table


def generate_correlation_plot(report, n_atoms, title):
    correlation_table = calculate_correlation(report, n_atoms)

    source = ColumnDataSource(
        data={
            "x": [0],
            "y": [0],
            "dw": [n_atoms],
            "dh": [n_atoms],
            "image": [correlation_table],
        }
    )

    plt = figure(
        title=title,
        x_axis_label="index i",
        y_axis_label="index j",
        x_range=(0, n_atoms),
        y_range=(0, n_atoms),
        toolbar_location="right",
        tools="save",
    )

    plt.title.text_font_size = "20pt"
    plt.axis.axis_label_text_font_size = "15pt"
    plt.axis.major_label_text_font_size = "10pt"

    color_mapper = LinearColorMapper(palette="Plasma256")

    image = plt.image(
        source=source,
        color_mapper=color_mapper,
    )

    color_bar = ColorBar(
        color_mapper=color_mapper, ticker=BasicTicker(), location=(0, 0)
    )

    plt.add_layout(color_bar, "right")

    plt.add_tools(CrosshairTool())
    plt.add_tools(
        HoverTool(
            renderers=[image],
            tooltips=[("Correlation", "@image")],
        )
    )

    return plt


show(generate_correlation_plot(emu_job, 11, "Simulated Correlation"))

show(generate_correlation_plot(hw_job, 11, "Actual Correlation"))
