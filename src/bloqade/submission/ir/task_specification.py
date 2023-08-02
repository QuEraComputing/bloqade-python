from pydantic import BaseModel
from typing import Optional, List, Tuple, Union
from decimal import Decimal

from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource, Step
from bokeh.layouts import gridplot

from bloqade.submission.ir.capabilities import QuEraCapabilities
from bloqade.ir.location import ListOfLocations
from bokeh.layouts import row

__all__ = ["QuEraTaskSpecification"]

# TODO: add version to these models.

FloatType = Union[Decimal, float]


def discretize_list(list_of_values: list, resolution: FloatType):
    resolution = Decimal(str(float(resolution)))
    return [round(Decimal(value) / resolution) * resolution for value in list_of_values]


class GlobalField(BaseModel):
    times: List[FloatType]
    values: List[FloatType]

    def __hash__(self):
        return hash((GlobalField, tuple(self.times), tuple(self.values)))


class LocalField(BaseModel):
    times: List[FloatType]
    values: List[FloatType]
    lattice_site_coefficients: List[FloatType]

    def __hash__(self):
        return hash(
            (
                LocalField,
                tuple(self.times),
                tuple(self.values),
                tuple(self.lattice_site_coefficients),
            )
        )


class RabiFrequencyAmplitude(BaseModel):
    global_: GlobalField

    class Config:
        allow_population_by_field_name = True
        fields = {"global_": "global"}

    def __hash__(self):
        return hash((RabiFrequencyAmplitude, self.global_))

    def discretize(self, task_capabilities: QuEraCapabilities):
        global_time_resolution = (
            task_capabilities.capabilities.rydberg.global_.time_resolution
        )
        global_value_resolution = (
            task_capabilities.capabilities.rydberg.global_.rabi_frequency_resolution
        )

        return RabiFrequencyAmplitude(
            global_=GlobalField(
                times=discretize_list(self.global_.times, global_time_resolution),
                values=discretize_list(self.global_.values, global_value_resolution),
            )
        )

    def _get_data_source(self):
        # isolate this for binding glyph later
        src = {
            "times_amp": [float(i) for i in self.global_.times],
            "values_amp": [float(i) for i in self.global_.values],
            "values_floor_amp": [0.0] * len(self.global_.values),
        }

        return src

    def figure(self, source, **fig_kwargs):
        line_plt = figure(
            **fig_kwargs,
            x_axis_label="Time (s)",
            y_axis_label="Value (rad/s)",
        )

        line_plt.x_range.start = 0
        line_plt.y_range.start = min(source.data["values_amp"]) - 5e6
        line_plt.y_range.end = max(source.data["values_amp"]) + 5e6

        line_plt.line(
            x="times_amp", y="values_amp", source=source, line_width=2, color="black"
        )

        line_plt.circle(
            x="times_amp", y="values_amp", source=source, size=4, color="black"
        )

        line_plt.varea(
            x="times_amp",
            y1="values_amp",
            y2="values_floor_amp",
            source=source,
            fill_alpha=0.3,
            color="#6437FF",
        )

        return line_plt

    def show(self):
        show(self.figure(ColumnDataSource(self._get_data_source())))


class RabiFrequencyPhase(BaseModel):
    global_: GlobalField

    class Config:
        allow_population_by_field_name = True
        fields = {"global_": "global"}

    def __hash__(self):
        return hash((RabiFrequencyPhase, self.global_))

    def discretize(self, task_capabilities: QuEraCapabilities):
        global_time_resolution = (
            task_capabilities.capabilities.rydberg.global_.time_resolution
        )
        global_value_resolution = (
            task_capabilities.capabilities.rydberg.global_.phase_resolution
        )

        return RabiFrequencyPhase(
            global_=GlobalField(
                times=discretize_list(self.global_.times, global_time_resolution),
                values=discretize_list(self.global_.values, global_value_resolution),
            )
        )

    def _get_data_source(self):
        # isolate this for binding glyph later
        src = {
            "times_phase": [float(i) for i in self.global_.times],
            "values_phase": [float(i) for i in self.global_.values],
        }

        return src

    def figure(self, source, **fig_kwargs):
        line_plt = figure(
            **fig_kwargs,
            x_axis_label="Time (s)",
            y_axis_label="Value (rad)",
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

    def show(self):
        show(self.figure(ColumnDataSource(self._get_data_source())))


class Detuning(BaseModel):
    global_: GlobalField
    local: Optional[LocalField]

    class Config:
        allow_population_by_field_name = True
        fields = {"global_": "global"}

    def __hash__(self):
        return hash((Detuning, self.global_, self.local))

    def discretize(self, task_capabilities: QuEraCapabilities):
        global_time_resolution = (
            task_capabilities.capabilities.rydberg.global_.time_resolution
        )
        global_value_resolution = (
            task_capabilities.capabilities.rydberg.global_.detuning_resolution
        )
        local_time_resolution = (
            task_capabilities.capabilities.rydberg.local.time_resolution
        )

        if self.local is not None:
            self.local = LocalField(
                times=discretize_list(self.local.times, local_time_resolution),
                values=self.local.values,
                lattice_site_coefficients=self.local.lattice_site_coefficients,
            )

        return Detuning(
            global_=GlobalField(
                times=discretize_list(self.global_.times, global_time_resolution),
                values=discretize_list(self.global_.values, global_value_resolution),
            ),
            local=self.local,
        )

    def _get_data_source(self):
        # isolate this for binding glyph later
        src = {
            "times_detune": [float(i) for i in self.global_.times],
            "values_detune": [float(i) for i in self.global_.values],
            "values_floor_detune": [0.0] * len(self.global_.values),
        }

        return src

    def global_figure(self, source, **fig_kwargs):
        line_plt = figure(
            **fig_kwargs, x_axis_label="Time (s)", y_axis_label="Value (rad/s)"
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

    def show_global(self):
        show(self.global_figure(ColumnDataSource(self._get_data_source())))


class RydbergHamiltonian(BaseModel):
    rabi_frequency_amplitude: RabiFrequencyAmplitude
    rabi_frequency_phase: RabiFrequencyPhase
    detuning: Detuning

    def __hash__(self):
        return hash(
            (
                RydbergHamiltonian,
                self.rabi_frequency_amplitude,
                self.rabi_frequency_phase,
                self.detuning,
            )
        )

    def discretize(self, task_capabilities: QuEraCapabilities):
        return RydbergHamiltonian(
            rabi_frequency_amplitude=self.rabi_frequency_amplitude.discretize(
                task_capabilities
            ),
            rabi_frequency_phase=self.rabi_frequency_phase.discretize(
                task_capabilities
            ),
            detuning=self.detuning.discretize(task_capabilities),
        )


class EffectiveHamiltonian(BaseModel):
    rydberg: RydbergHamiltonian

    def __hash__(self):
        return hash((EffectiveHamiltonian, self.rydberg))

    def discretize(self, task_capabilities: QuEraCapabilities):
        return EffectiveHamiltonian(rydberg=self.rydberg.discretize(task_capabilities))


class Lattice(BaseModel):
    sites: List[Tuple[FloatType, FloatType]]
    filling: List[int]

    def __hash__(self):
        return hash((Lattice, tuple(self.sites), tuple(self.filling)))

    def discretize(self, task_capabilities: QuEraCapabilities):
        position_resolution = (
            task_capabilities.capabilities.lattice.geometry.position_resolution
        )
        return Lattice(
            sites=[discretize_list(site, position_resolution) for site in self.sites],
            filling=self.filling,
        )

    def figure(self):
        ## use ir.Atom_oarrangement's plotting:
        reg = ListOfLocations().add_positions(self.sites, self.filling)
        fig_reg = reg.figure()  # ignore the B-rad widget
        return fig_reg

    def show(self):
        show(self.figure())


class QuEraTaskSpecification(BaseModel):
    nshots: int
    lattice: Lattice
    effective_hamiltonian: EffectiveHamiltonian

    def __hash__(self):
        return hash(
            (
                QuEraTaskSpecification,
                self.nshots,
                self.lattice,
                self.effective_hamiltonian,
            )
        )

    def discretize(self, task_capabilities: QuEraCapabilities):
        return QuEraTaskSpecification(
            nshots=self.nshots,
            lattice=self.lattice.discretize(task_capabilities),
            effective_hamiltonian=self.effective_hamiltonian.discretize(
                task_capabilities
            ),
        )

    def figure(self):
        # grab all the datas and combine them:
        rabi_amp_src = (
            self.effective_hamiltonian.rydberg.rabi_frequency_amplitude._get_data_source()
        )
        rabi_phase_src = (
            self.effective_hamiltonian.rydberg.rabi_frequency_phase._get_data_source()
        )
        global_detuning_src = (
            self.effective_hamiltonian.rydberg.detuning._get_data_source()
        )

        rabi_amp_src = ColumnDataSource(rabi_amp_src)
        rabi_phase_src = ColumnDataSource(rabi_phase_src)
        global_detuning_src = ColumnDataSource(global_detuning_src)

        # grab global figures
        rabi_amplitude = (
            self.effective_hamiltonian.rydberg.rabi_frequency_amplitude.figure(
                rabi_amp_src, tools="hover,wheel_zoom,reset, undo, redo, pan"
            )
        )

        rabi_phase = self.effective_hamiltonian.rydberg.rabi_frequency_phase.figure(
            rabi_phase_src,
            x_range=rabi_amplitude.x_range,
            tools="hover,wheel_zoom,reset, undo, redo, pan",
        )
        global_detuning = self.effective_hamiltonian.rydberg.detuning.global_figure(
            global_detuning_src,
            x_range=rabi_amplitude.x_range,
            tools="hover,wheel_zoom,reset, undo, redo, pan",
        )

        # lattice:
        register = self.lattice.figure()

        full_plt = gridplot(
            [[rabi_amplitude], [global_detuning], [rabi_phase]],
            merge_tools=False,
            sizing_mode="stretch_both",
        )
        # full_plt.width_policy = "max"

        full_plt = row(full_plt, register)
        full_plt.width_policy = "max"
        full_plt.sizing_mode = "stretch_both"

        return full_plt

    def show(self):
        show(self.figure())
