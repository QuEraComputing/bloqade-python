from pydantic import BaseModel
from typing import Optional, List, Tuple, Union
from decimal import Decimal

from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource, Step
from bokeh.layouts import gridplot

from bloqade.submission.ir.capabilities import QuEraCapabilities


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

    def figure(self):
        source = ColumnDataSource(
            {
                "times": [float(i) for i in self.global_.times],
                "values": [float(i) for i in self.global_.values],
                "values_floor": [0.0] * len(self.global_.values),
            }
        )

        line_plt = figure(
            x_axis_label="Time (s)",
            y_axis_label="Value (rad/s)",
        )

        line_plt.x_range.start = 0
        line_plt.y_range.start = 0

        line_plt.line(x="times", y="values", source=source, line_width=2, color="black")

        line_plt.circle(x="times", y="values", source=source, size=4, color="black")

        line_plt.varea(
            x="times",
            y1="values",
            y2="values_floor",
            source=source,
            fill_alpha=0.3,
            color="#6437FF",
        )

        return line_plt

    def show(self):
        show(self.figure())


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

    def figure(self):
        source = ColumnDataSource(
            {
                "times": [float(i) for i in self.global_.times],
                "values": [float(i) for i in self.global_.values],
            }
        )

        line_plt = figure(
            x_axis_label="Time (s)",
            y_axis_label="Value (rad)",
        )

        line_plt.y_range.start = 0
        line_plt.x_range.start = 0

        steps = Step(
            x="times", y="values", line_color="black", line_width=2, mode="center"
        )

        line_plt.add_glyph(source, steps)

        line_plt.circle(x="times", y="values", source=source, size=4, color="black")

        return line_plt

    def show(self):
        show(self.figure())


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

    def global_figure(self):
        source = ColumnDataSource(
            {
                "times": [float(i) for i in self.global_.times],
                "values": [float(i) for i in self.global_.values],
                "values_floor": [0.0] * len(self.global_.values),
            }
        )

        line_plt = figure(
            x_axis_label="Time (s)",
            y_axis_label="Value (rad/s)",
        )

        line_plt.y_range.start = 0
        line_plt.x_range.start = 0

        line_plt.line(x="times", y="values", source=source, line_width=2, color="black")

        line_plt.circle(x="times", y="values", source=source, size=4, color="black")

        line_plt.varea(
            x="times",
            y1="values",
            y2="values_floor",
            source=source,
            fill_alpha=0.5,
            color="#EFD0DE",
        )

        return line_plt

    def show_global(self):
        show(self.global_figure())


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
        # grab global figures
        rabi_amplitude = (
            self.effective_hamiltonian.rydberg.rabi_frequency_amplitude.figure()
        )
        rabi_phase = self.effective_hamiltonian.rydberg.rabi_frequency_phase.figure()
        global_detuning = self.effective_hamiltonian.rydberg.detuning.global_figure()

        full_plt = gridplot(
            [[rabi_amplitude], [global_detuning], [rabi_phase]],
            merge_tools=False,
            sizing_mode="stretch_both",
        )

        full_plt.width_policy = "max"

        return full_plt

    def show(self):
        show(self.figure())
