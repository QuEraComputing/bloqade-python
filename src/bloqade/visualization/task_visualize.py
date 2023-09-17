from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, Step, HoverTool
from bokeh.layouts import gridplot, row


def get_task_ir_figure(task_ir, **fig_kwargs):
    from bloqade.submission.ir.task_specification import (
        RabiFrequencyAmplitude,
        RabiFrequencyPhase,
        Detuning,
        Lattice,
        QuEraTaskSpecification,
    )

    if isinstance(task_ir, RabiFrequencyAmplitude):
        return get_rabi_amp_figure(task_ir, **fig_kwargs)
    elif isinstance(task_ir, RabiFrequencyPhase):
        return get_rabi_phase_figure(task_ir, **fig_kwargs)
    elif isinstance(task_ir, Detuning):
        return get_detune_figure(task_ir, **fig_kwargs)
    elif isinstance(task_ir, Lattice):
        return get_lattice_figure(task_ir, **fig_kwargs)
    elif isinstance(task_ir, QuEraTaskSpecification):
        return get_quera_task_figure(task_ir, **fig_kwargs)
    else:
        raise NotImplementedError(
            f"not supported task IR for figure, got {type(task_ir)}"
        )


def get_lattice_figure(lattice, **fig_kwargs):
    from bloqade.ir.location import ListOfLocations

    ## use ir.Atom_oarrangement's plotting:
    ## covert unit to m -> um
    sites_um = list(
        map(lambda cord: (float(cord[0]) * 1e6, float(cord[1]) * 1e6), lattice.sites)
    )
    reg = ListOfLocations().add_position(sites_um, lattice.filling)
    fig_reg = reg.figure(fig_kwargs=fig_kwargs)  # ignore the B-rad widget
    return fig_reg


def get_quera_task_figure(task_ir, **fig_kwargs):
    # grab global figures
    rabi_amplitude = (
        task_ir.effective_hamiltonian.rydberg.rabi_frequency_amplitude.figure(
            tools="wheel_zoom,reset, undo, redo, pan"
        )
    )
    rabi_phase = task_ir.effective_hamiltonian.rydberg.rabi_frequency_phase.figure(
        x_range=rabi_amplitude.x_range,
        tools="hover,wheel_zoom,reset, undo, redo, pan",
    )
    global_detuning = task_ir.effective_hamiltonian.rydberg.detuning.global_figure(
        x_range=rabi_amplitude.x_range,
        tools="hover,wheel_zoom,reset, undo, redo, pan",
    )

    # lattice:
    register = task_ir.lattice.figure(x_axis_label="x (um)", y_axis_label="y (um)")

    col_plt = gridplot(
        [[rabi_amplitude], [global_detuning], [rabi_phase]],
        merge_tools=False,
        sizing_mode="stretch_both",
    )
    col_plt.width_policy = "max"

    full_plt = row(col_plt, register, sizing_mode="stretch_both")
    full_plt.width_policy = "max"

    return full_plt


def get_rabi_phase_figure(rabi_phase, **fig_kwargs):
    source = ColumnDataSource(rabi_phase._get_data_source())
    TOOLTIPS = [("(x,y)", "(@times_phase, @values_phase)")]

    line_plt = figure(
        **fig_kwargs,
        tooltips=TOOLTIPS,
        x_axis_label="Time (s)",
        y_axis_label="ϕ(t) (rad)",
    )

    line_plt.y_range.start = min(source.data["values_phase"]) - 5e6
    line_plt.y_range.end = max(source.data["values_phase"]) + 5e6
    line_plt.x_range.start = 0

    steps = Step(
        x="times_phase",
        y="values_phase",
        line_color="black",
        line_width=2,
        mode="center",
    )

    line_plt.add_glyph(source, steps)

    line_plt.circle(
        x="times_phase", y="values_phase", source=source, size=4, color="black"
    )

    return line_plt


def get_rabi_amp_figure(rabi_amp, **fig_kwargs):
    source = ColumnDataSource(rabi_amp._get_data_source())
    hover = HoverTool()
    hover.tooltips = [("(x,y)", "(@times_amp, @values_amp)")]

    line_plt = figure(
        **fig_kwargs,
        x_axis_label="Time (s)",
        y_axis_label="Ω(t) (rad/s)",
    )

    line_plt.x_range.start = 0
    line_plt.y_range.start = min(source.data["values_amp"]) - 5e6
    line_plt.y_range.end = max(source.data["values_amp"]) + 5e6

    line_plt.line(
        x="times_amp", y="values_amp", source=source, line_width=2, color="black"
    )

    line_plt.circle(x="times_amp", y="values_amp", source=source, size=4, color="black")

    line_plt.varea(
        x="times_amp",
        y1="values_amp",
        y2="values_floor_amp",
        source=source,
        fill_alpha=0.3,
        color="#6437FF",
    )
    line_plt.add_tools(hover)

    return line_plt


def get_detune_figure(detune, **fig_kwargs):
    source = ColumnDataSource(detune._get_data_source())
    TOOLTIPS = [("(x,y)", "(@times_detune, @values_detune)")]

    line_plt = figure(
        **fig_kwargs,
        tooltips=TOOLTIPS,
        x_axis_label="Time (s)",
        y_axis_label="Δ(t) (rad/s)",
    )

    line_plt.x_range.start = 0

    line_plt.y_range.start = min(source.data["values_detune"]) - 5e6
    line_plt.y_range.end = max(source.data["values_detune"]) + 5e6

    line_plt.line(
        x="times_detune",
        y="values_detune",
        source=source,
        line_width=2,
        color="black",
    )

    line_plt.circle(
        x="times_detune", y="values_detune", source=source, size=4, color="black"
    )

    line_plt.varea(
        x="times_detune",
        y1="values_detune",
        y2="values_floor_detune",
        source=source,
        fill_alpha=0.5,
        color="#EFD0DE",
    )

    return line_plt
