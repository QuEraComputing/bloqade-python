from bokeh.models import ColumnDataSource
from bokeh.layouts import gridplot, row
from bloqade.ir.location import ListOfLocations


def get_lattice_figure(lattice, fig_kwargs):
    ## use ir.Atom_oarrangement's plotting:
    ## covert unit to m -> um
    sites_um = list(
        map(lambda cord: (float(cord[0]) * 1e6, float(cord[1]) * 1e6), lattice.sites)
    )
    reg = ListOfLocations().add_positions(sites_um, lattice.filling)
    fig_reg = reg.figure(fig_kwargs=fig_kwargs)  # ignore the B-rad widget
    return fig_reg


def get_quera_task_figure(task_ir):
    # grab all the datas and combine them:
    rabi_amp_src = (
        task_ir.effective_hamiltonian.rydberg.rabi_frequency_amplitude._get_data_source()
    )
    rabi_phase_src = (
        task_ir.effective_hamiltonian.rydberg.rabi_frequency_phase._get_data_source()
    )
    global_detuning_src = (
        task_ir.effective_hamiltonian.rydberg.detuning._get_data_source()
    )

    rabi_amp_src = ColumnDataSource(rabi_amp_src)
    rabi_phase_src = ColumnDataSource(rabi_phase_src)
    global_detuning_src = ColumnDataSource(global_detuning_src)

    # grab global figures
    rabi_amplitude = (
        task_ir.effective_hamiltonian.rydberg.rabi_frequency_amplitude.figure(
            rabi_amp_src, tools="wheel_zoom,reset, undo, redo, pan"
        )
    )

    rabi_phase = task_ir.effective_hamiltonian.rydberg.rabi_frequency_phase.figure(
        rabi_phase_src,
        x_range=rabi_amplitude.x_range,
        tools="hover,wheel_zoom,reset, undo, redo, pan",
    )
    global_detuning = task_ir.effective_hamiltonian.rydberg.detuning.global_figure(
        global_detuning_src,
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
