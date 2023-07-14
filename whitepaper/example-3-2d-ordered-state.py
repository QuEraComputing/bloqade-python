from bloqade.ir.location import Square
from bloqade.task import HardwareFuture

from bokeh.plotting import figure, show
from bokeh.palettes import interp_palette
from bokeh.models import (
    ColumnDataSource,
    LinearColorMapper,
    ColorBar,
    BasicTicker,
    CrosshairTool,
    HoverTool,
)
import numpy as np

n_atoms = 11
lattice_const = 5.9

rabi_amplitude_values = [0.0, 15.8, 15.8, 0.0]
rabi_detuning_values = [-16.33, -16.33, "delta_end", "delta_end"]
durations = [0.8, "sweep_time", 0.8]

ordered_state_2D_prog = (
    Square(n_atoms, lattice_const)
    .rydberg.rabi.amplitude.uniform.piecewise_linear(durations, rabi_amplitude_values)
    .detuning.uniform.piecewise_linear(durations, rabi_detuning_values)
)

ordered_state_2D_job = ordered_state_2D_prog.assign(delta_end=42.66, sweep_time=2.4)

# Can only run on HW because 121 atoms infeasible on simulator
"""
(
    ordered_state_2D_job.braket(100)
    .submit()
    .save_json("example-3-ordered-state-2D-job.json")
)
"""

# retrieve results from HW
hw_future = HardwareFuture()
hw_future.load_json("example-3-ordered-state-2D-job.json")
hw_job = hw_future.report()

# Plots
## Standard Density Plot
density_plt_source = ColumnDataSource(
    data={
        "x": [0],
        "y": [0],
        "dw": [n_atoms],
        "dh": [n_atoms],
        "image": [hw_job.rydberg_densities().to_numpy().reshape(n_atoms, n_atoms)],
    }
)

density_plt = figure(
    title="Striated Phase, 5.90 μm spacing",
    x_range=(0, n_atoms),
    y_range=(0, n_atoms),
    toolbar_location="right",
    tools="save",
)

density_plt.title.text_font_size = "20pt"

density_color_mapper = LinearColorMapper(palette="Plasma256")

density_image = density_plt.image(
    source=density_plt_source,
    color_mapper=density_color_mapper,
)

density_color_bar = ColorBar(
    color_mapper=density_color_mapper, ticker=BasicTicker(), location=(0, 0)
)

density_plt.add_layout(density_color_bar, "right")

density_plt.add_tools(CrosshairTool())

density_plt.add_tools(
    HoverTool(renderers=[density_image], tooltips=[("Density", "@image")])
)

show(density_plt)


## two point correlation plot
def in_bounds(x, y, n_atoms_square):
    if x >= 0 and x <= n_atoms_square - 1 and y >= 0 and y <= n_atoms_square - 1:
        return True

    return False


def G2(site_k, site_l, n_atoms_square, report):
    # reshape densities to matrix from list, makes it easier for indexing
    density_table = (
        report.rydberg_densities().to_numpy().reshape(n_atoms_square, n_atoms_square)
    )

    # Reshape shots to make it easier to calculate <n_i * n_j>
    # Convert each shot into a matrix, go from (n shots, flat list)
    # to (n shots, atom rows, columns
    n_rows_shots = report.bitstrings[0].shape[0]  # preserve number of rows
    shots = report.bitstrings[0].reshape(n_rows_shots, n_atoms_square, n_atoms_square)

    running_corr_sum = 0.0
    n_atom_pairs = 0  # use to calculate final average
    for x in range(n_atoms_square):
        for y in range(n_atoms_square):
            if in_bounds(x + site_k, y + site_l, n_atoms_square):
                n_atom_pairs += 1
                running_corr_sum += (
                    (1 - shots[:, x, y]) * (1 - shots[:, x + site_k, y + site_l])
                ).mean() - density_table[x, y] * density_table[
                    x + site_k, y + site_l
                ]  # <n_i * n_j> - <n_i> * <n_j>

    return running_corr_sum / n_atom_pairs


def get_two_point_correlation(report, n_atoms_square):
    # can go from -k, k
    site_k = site_l = n_atoms_square - 1

    G2_table = np.zeros(((2 * site_k) + 1, (2 * site_l) + 1))

    for a_idx, a in enumerate(range(-site_k, site_k + 1)):
        for b_idx, b in enumerate(range(-site_l, site_l + 1)):
            G2_table[a_idx, b_idx] = G2(a, b, n_atoms_square, report)

    return G2_table


two_pt_corr = get_two_point_correlation(hw_job, n_atoms)

# figure out x and y start and end
site_k = site_l = n_atoms - 1

two_pt_corr_plt_source = ColumnDataSource(
    data={
        "image": [two_pt_corr],
        "x": [-site_k],
        "y": [-site_l],
        "dw": [two_pt_corr.shape[0]],
        "dh": [two_pt_corr.shape[1]],
    }
)

two_pt_corr_plt = figure(
    title="G²(k,l)",
    x_axis_label="k",
    y_axis_label="l",
    x_range=(-site_k, site_k),
    y_range=(-site_l, site_l),
    toolbar_location="right",
    tools="save",
)

two_pt_corr_plt.title.text_font_size = "20pt"
two_pt_corr_plt.axis.axis_label_text_font_size = "15pt"
two_pt_corr_plt.axis.major_label_text_font_size = "10pt"

two_pt_corr_plt_color_mapper = LinearColorMapper(
    palette=interp_palette(["#6437FF", "#FFFFFF", "#FF505D"], 256),
    high=two_pt_corr.max(),
    low=-two_pt_corr.max(),
)

two_pt_corr_plt_image = two_pt_corr_plt.image(
    source=two_pt_corr_plt_source,
    color_mapper=two_pt_corr_plt_color_mapper,
)

color_bar = ColorBar(
    color_mapper=two_pt_corr_plt_color_mapper, ticker=BasicTicker(), location=(0, 0)
)

two_pt_corr_plt.add_layout(color_bar, "right")

two_pt_corr_plt.add_tools(CrosshairTool())
two_pt_corr_plt.add_tools(
    HoverTool(renderers=[two_pt_corr_plt_image], tooltips=[("Correlation", "@image")])
)

show(two_pt_corr_plt)
