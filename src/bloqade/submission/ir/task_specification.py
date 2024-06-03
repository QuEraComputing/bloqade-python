"""
This module defines data models for QuEra task specifications using the Pydantic library. 
It includes models for various components such as Rabi frequency amplitude, Rabi frequency phase,
detuning, and lattice configurations. These models support discretization based on task capabilities
and provide methods for visualization.
"""

from typing import Optional, List, Tuple
from decimal import Decimal
from pydantic.v1 import BaseModel
from bloqade.submission.ir.capabilities import QuEraCapabilities
from bloqade.visualization import display_task_ir, get_task_ir_figure

__all__ = ["QuEraTaskSpecification"]

# TODO: add version to these models.

FloatType = Decimal


def discretize_list(list_of_values: list, resolution: FloatType):
    """
    Discretizes a list of values based on the given resolution.

    Args:
       list_of_values (list): List of values to be discretized.
       resolution (FloatType): Resolution to which values should be discretized.

    Returns:
       list: Discretized list of values.
    """
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
        """
        Discretizes the global field values based on the task capabilities.

        Args:
           task_capabilities (QuEraCapabilities): Capabilities of the task for discretization.

        Returns:
           RabiFrequencyAmplitude: Discretized Rabi frequency amplitude.
        """
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
        """
        Prepares data source for visualization.

        Returns:
           dict: Data source dictionary for visualization.
        """
        # isolate this for binding glyph later
        # required by visualization
        src = {
            "times_amp": [float(i) for i in self.global_.times],
            "values_amp": [float(i) for i in self.global_.values],
            "values_floor_amp": [0.0] * len(self.global_.values),
        }

        return src

    def figure(self, **fig_kwargs):
        """
        Generates figure for the Rabi frequency amplitude.

        Args:
           **fig_kwargs: Additional keyword arguments for figure customization.

        Returns:
           Figure: Visualization figure for the Rabi frequency amplitude.
        """
        return get_task_ir_figure(self, **fig_kwargs)

    def show(self):
        """
        Displays the Rabi frequency amplitude.
        """
        display_task_ir(self)


class RabiFrequencyPhase(BaseModel):
    global_: GlobalField

    class Config:
        allow_population_by_field_name = True
        fields = {"global_": "global"}

    def __hash__(self):
        return hash((RabiFrequencyPhase, self.global_))

    def discretize(self, task_capabilities: QuEraCapabilities):
        """
        Discretizes the global field values based on the task capabilities.

        Args:
           task_capabilities (QuEraCapabilities): Capabilities of the task for discretization.

        Returns:
           RabiFrequencyPhase: Discretized Rabi frequency phase.
        """
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
        """
        Prepares data source for visualization.

        Returns:
           dict: Data source dictionary for visualization.
        """
        # isolate this for binding glyph later
        src = {
            "times_phase": [float(i) for i in self.global_.times],
            "values_phase": [float(i) for i in self.global_.values],
        }

        return src

    def figure(self, **fig_kwargs):
        """
        Generates figure for the Rabi frequency phase.

        Args:
           **fig_kwargs: Additional keyword arguments for figure customization.

        Returns:
           Figure: Visualization figure for the Rabi frequency phase.
        """
        ## fig_kwargs is for extra tuning when assemble
        ## e.g. calling from QuEraTaskSpecification.figure()
        return get_task_ir_figure(self, **fig_kwargs)

    def show(self):
        """
        Displays the Rabi frequency phase.
        """
        # we dont need fig_kwargs when display alone
        display_task_ir(self)


class Detuning(BaseModel):
    global_: GlobalField
    local: Optional[LocalField]

    class Config:
        allow_population_by_field_name = True
        fields = {"global_": "global"}

    def __hash__(self):
        return hash((Detuning, self.global_, self.local))

    def discretize(self, task_capabilities: QuEraCapabilities):
        """
        Discretizes the global and local field values based on the task capabilities.

        Args:
           task_capabilities (QuEraCapabilities): Capabilities of the task for discretization.

        Returns:
           Detuning: Discretized detuning fields.
        """
        global_time_resolution = (
            task_capabilities.capabilities.rydberg.global_.time_resolution
        )
        global_value_resolution = (
            task_capabilities.capabilities.rydberg.global_.detuning_resolution
        )

        if self.local is not None:
            local_time_resolution = (
                task_capabilities.capabilities.rydberg.local.time_resolution
            )
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
        """
        Prepares data source for visualization.

        Returns:
           dict: Data source dictionary for visualization.
        """
        # isolate this for binding glyph later
        src = {
            "times_detune": [float(i) for i in self.global_.times],
            "values_detune": [float(i) for i in self.global_.values],
            "values_floor_detune": [0.0] * len(self.global_.values),
        }

        return src

    def global_figure(self, **fig_kwargs):
        """
        Generates figure for the global detuning.

        Args:
           **fig_kwargs: Additional keyword arguments for figure customization.

        Returns:
           Figure: Visualization figure for the global detuning.
        """
        return get_task_ir_figure(self, **fig_kwargs)

    def show_global(self):
        """
        Displays the global detuning.
        """
        display_task_ir(self)


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
        """
        Discretizes the Rydberg Hamiltonian based on the task capabilities.

        Args:
           task_capabilities (QuEraCapabilities): Capabilities of the task for discretization.

        Returns:
           RydbergHamiltonian: Discretized Rydberg Hamiltonian.
        """
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
        """
        Discretizes the effective Hamiltonian based on the task capabilities.

        Args:
           task_capabilities (QuEraCapabilities): Capabilities of the task for discretization.

        Returns:
           EffectiveHamiltonian: Discretized effective Hamiltonian.
        """
        return EffectiveHamiltonian(rydberg=self.rydberg.discretize(task_capabilities))


class Lattice(BaseModel):
    sites: List[Tuple[FloatType, FloatType]]
    filling: List[int]

    def __hash__(self):
        return hash((Lattice, tuple(self.sites), tuple(self.filling)))

    def discretize(self, task_capabilities: QuEraCapabilities):
        """
        Discretizes the lattice sites based on the task capabilities.

        Args:
           task_capabilities (QuEraCapabilities): Capabilities of the task for discretization.

        Returns:
           Lattice: Discretized lattice.
        """
        position_resolution = (
            task_capabilities.capabilities.lattice.geometry.position_resolution
        )
        return Lattice(
            sites=[discretize_list(site, position_resolution) for site in self.sites],
            filling=self.filling,
        )

    def figure(self, **fig_kwargs):
        """
        Generates figure for the lattice.

        Args:
           **fig_kwargs: Additional keyword arguments for figure customization.

        Returns:
           Figure: Visualization figure for the lattice.
        """
        ## use ir.Atom_oarrangement's plotting:
        ## covert unit to m -> um
        return get_task_ir_figure(self, **fig_kwargs)

    def show(self):
        """
        Displays the lattice.
        """
        display_task_ir(self)


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
        """
        Discretizes the task specification based on the task capabilities.

        Args:
           task_capabilities (QuEraCapabilities): Capabilities of the task for discretization.

        Returns:
           QuEraTaskSpecification: Discretized task specification.
        """
        return QuEraTaskSpecification(
            nshots=self.nshots,
            lattice=self.lattice.discretize(task_capabilities),
            effective_hamiltonian=self.effective_hamiltonian.discretize(
                task_capabilities
            ),
        )

    def figure(self):
        """
        Generates figure for the task specification.

        Returns:
           Figure: Visualization figure for the task specification.
        """
        return get_task_ir_figure(self)

    def show(self):
        """
        Displays the task specification.
        """
        display_task_ir(self)
