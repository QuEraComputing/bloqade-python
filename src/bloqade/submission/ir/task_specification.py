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

    Example:
        ```python
        from decimal import Decimal

        values = [Decimal('0.1'), Decimal('0.2'), Decimal('0.3')]
        resolution = Decimal('0.05')
        discretized_values = discretize_list(values, resolution)
        print(discretized_values)  # [Decimal('0.1'), Decimal('0.2'), Decimal('0.3')]
        ```
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

    def discretize(self, device_capabilities: QuEraCapabilities):
        """
        Discretizes the global field values based on the task capabilities.

        Args:
           device_capabilities (QuEraCapabilities): Capabilities of the task for discretization.

        Returns:
           RabiFrequencyAmplitude: Discretized Rabi frequency amplitude.

        Example:
            ```python
            from decimal import Decimal
            from bloqade.submission.ir.capabilities import QuEraCapabilities

            # Example values for the global field
            times = [Decimal('0.0'), Decimal('1.0'), Decimal('2.0')]
            values = [Decimal('0.1'), Decimal('0.2'), Decimal('0.3')]

            # Create a GlobalField
            global_field = GlobalField(times=times, values=values)

            # Create a RabiFrequencyAmplitude
            rabi_frequency_amplitude = RabiFrequencyAmplitude(global_=global_field)

            # Define example capabilities
            class RydbergCapabilities:
                class GlobalCapabilities:
                    time_resolution = Decimal('0.5')
                    rabi_frequency_resolution = Decimal('0.1')

                global_ = GlobalCapabilities()

            class Capabilities:
                rydberg = RydbergCapabilities()

            device_capabilities = QuEraCapabilities(capabilities=Capabilities())

            # Discretize the RabiFrequencyAmplitude based on the task capabilities
            discretized_rabi_amplitude = rabi_frequency_amplitude.discretize(device_capabilities)
            print(discretized_rabi_amplitude)
            ```
        """
        global_time_resolution = (
            device_capabilities.capabilities.rydberg.global_.time_resolution
        )
        global_value_resolution = (
            device_capabilities.capabilities.rydberg.global_.rabi_frequency_resolution
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

        Example:
            ```python
            from decimal import Decimal
            from bloqade.visualization import show

            # Example values for the global field
            times = [Decimal('0.0'), Decimal('1.0'), Decimal('2.0')]
            values = [Decimal('0.1'), Decimal('0.2'), Decimal('0.3')]

            # Create a GlobalField
            global_field = GlobalField(times=times, values=values)

            # Create a RabiFrequencyAmplitude
            rabi_frequency_amplitude = RabiFrequencyAmplitude(global_=global_field)

            # Generate and display the figure
            rabi_amplitude_figure = rabi_frequency_amplitude.figure()
            show(rabi_amplitude_figure)
            ```
        """
        return get_task_ir_figure(self, **fig_kwargs)

    def show(self):
        """
        Displays the Rabi frequency amplitude.

        Example:
            ```python
            from decimal import Decimal

            # Example values for the global field
            times = [Decimal('0.0'), Decimal('1.0'), Decimal('2.0')]
            values = [Decimal('0.1'), Decimal('0.2'), Decimal('0.3')]

            # Create a GlobalField
            global_field = GlobalField(times=times, values=values)

            # Create a RabiFrequencyAmplitude
            rabi_frequency_amplitude = RabiFrequencyAmplitude(global_=global_field)

            # Display the Rabi frequency amplitude
            rabi_frequency_amplitude.show()
            ```
        """
        display_task_ir(self)


class RabiFrequencyPhase(BaseModel):
    global_: GlobalField

    class Config:
        allow_population_by_field_name = True
        fields = {"global_": "global"}

    def __hash__(self):
        return hash((RabiFrequencyPhase, self.global_))

    def discretize(self, device_capabilities: QuEraCapabilities):
        """
        Discretizes the global field values based on the task capabilities.

        Args:
           device_capabilities (QuEraCapabilities): Capabilities of the task for discretization.

        Returns:
           RabiFrequencyPhase: Discretized Rabi frequency phase.

        Example:
            ```python
            from decimal import Decimal
            from bloqade.submission.ir.capabilities import QuEraCapabilities

            # Example values for the global field
            times = [Decimal('0.0'), Decimal('1.0'), Decimal('2.0')]
            values = [Decimal('0.1'), Decimal('0.2'), Decimal('0.3')]

            # Create a GlobalField
            global_field = GlobalField(times=times, values=values)

            # Create a RabiFrequencyPhase
            rabi_frequency_phase = RabiFrequencyPhase(global_=global_field)

            # Define example capabilities
            class RydbergCapabilities:
                class GlobalCapabilities:
                    time_resolution = Decimal('0.5')
                    phase_resolution = Decimal('0.1')

                global_ = GlobalCapabilities()

            class Capabilities:
                rydberg = RydbergCapabilities()

            device_capabilities = QuEraCapabilities(capabilities=Capabilities())

            # Discretize the RabiFrequencyPhase based on the task capabilities
            discretized_rabi_phase = rabi_frequency_phase.discretize(device_capabilities)
            print(discretized_rabi_phase)
            ```
        """
        global_time_resolution = (
            device_capabilities.capabilities.rydberg.global_.time_resolution
        )
        global_value_resolution = (
            device_capabilities.capabilities.rydberg.global_.phase_resolution
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

        Example:
            ```python
            from decimal import Decimal
            from bloqade.visualization import show

            # Example values for the global field
            times = [Decimal('0.0'), Decimal('1.0'), Decimal('2.0')]
            values = [Decimal('0.1'), Decimal('0.2'), Decimal('0.3')]

            # Create a GlobalField
            global_field = GlobalField(times=times, values=values)

            # Create a RabiFrequencyPhase
            rabi_frequency_phase = RabiFrequencyPhase(global_=global_field)

            # Generate and display the figure
            rabi_phase_figure = rabi_frequency_phase.figure()
            show(rabi_phase_figure)
            ```
        """
        ## fig_kwargs is for extra tuning when assemble
        ## e.g. calling from QuEraTaskSpecification.figure()
        return get_task_ir_figure(self, **fig_kwargs)

    def show(self):
        """
        Displays the Rabi frequency phase.

        Example:
            ```python
            from decimal import Decimal

            # Example values for the global field
            times = [Decimal('0.0'), Decimal('1.0'), Decimal('2.0')]
            values = [Decimal('0.1'), Decimal('0.2'), Decimal('0.3')]

            # Create a GlobalField
            global_field = GlobalField(times=times, values=values)

            # Create a RabiFrequencyPhase
            rabi_frequency_phase = RabiFrequencyPhase(global_=global_field)

            # Display the Rabi frequency phase
            rabi_frequency_phase.show()
            ```
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

    def discretize(self, device_capabilities: QuEraCapabilities):
        """
        Discretizes the global and local field values based on the task capabilities.

        Args:
           device_capabilities (QuEraCapabilities): Capabilities of the task for discretization.

        Returns:
           Detuning: Discretized detuning fields.
        """
        global_time_resolution = (
            device_capabilities.capabilities.rydberg.global_.time_resolution
        )
        global_value_resolution = (
            device_capabilities.capabilities.rydberg.global_.detuning_resolution
        )

        if self.local is not None:
            local_time_resolution = (
                device_capabilities.capabilities.rydberg.local.time_resolution
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

            # Create a Detuning
            detuning = Detuning(global_=global_field)

            # Generate and display the figure
            detuning_figure = detuning.figure()
            show(detuning_figure)
            ```
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

    def discretize(self, device_capabilities: QuEraCapabilities):
        """
        Discretizes the Rydberg Hamiltonian based on the task capabilities.

        Args:
           device_capabilities (QuEraCapabilities): Capabilities of the task for discretization.

        Returns:
           RydbergHamiltonian: Discretized Rydberg Hamiltonian.

        Example:
            ```python
            from decimal import Decimal
            from bloqade.submission.ir.capabilities import QuEraCapabilities

            # Example values for the global fields
            times = [Decimal('0.0'), Decimal('1.0'), Decimal('2.0')]
            values = [Decimal('0.1'), Decimal('0.2'), Decimal('0.3')]

            # Create GlobalFields
            global_field_rabi_amplitude = GlobalField(times=times, values=values)
            global_field_rabi_phase = GlobalField(times=times, values=values)
            global_field_detuning = GlobalField(times=times, values=values)

            # Create RabiFrequencyAmplitude, RabiFrequencyPhase, and Detuning
            rabi_frequency_amplitude = RabiFrequencyAmplitude(global_=global_field_rabi_amplitude)
            rabi_frequency_phase = RabiFrequencyPhase(global_=global_field_rabi_phase)
            detuning = Detuning(global_=global_field_detuning)

            # Create RydbergHamiltonian
            rydberg_hamiltonian = RydbergHamiltonian(
                rabi_frequency_amplitude=rabi_frequency_amplitude,
                rabi_frequency_phase=rabi_frequency_phase,
                detuning=detuning
            )

            # Define example capabilities
            class RydbergCapabilities:
                class GlobalCapabilities:
                    time_resolution = Decimal('0.5')
                    rabi_frequency_resolution = Decimal('0.1')
                    phase_resolution = Decimal('0.1')
                    detuning_resolution = Decimal('0.1')

                global_ = GlobalCapabilities()

            class Capabilities:
                rydberg = RydbergCapabilities()

            device_capabilities = QuEraCapabilities(capabilities=Capabilities())

            # Discretize the RydbergHamiltonian based on the task capabilities
            discretized_rydberg_hamiltonian = rydberg_hamiltonian.discretize(device_capabilities)
            print(discretized_rydberg_hamiltonian)
            ```
        """
        return RydbergHamiltonian(
            rabi_frequency_amplitude=self.rabi_frequency_amplitude.discretize(
                device_capabilities
            ),
            rabi_frequency_phase=self.rabi_frequency_phase.discretize(
                device_capabilities
            ),
            detuning=self.detuning.discretize(device_capabilities),
        )


class EffectiveHamiltonian(BaseModel):
    rydberg: RydbergHamiltonian

    def __hash__(self):
        return hash((EffectiveHamiltonian, self.rydberg))

    def discretize(self, device_capabilities: QuEraCapabilities):
        """
        Discretizes the effective Hamiltonian based on the task capabilities.

        Args:
           device_capabilities (QuEraCapabilities): Capabilities of the task for discretization.

        Returns:
           EffectiveHamiltonian: Discretized effective Hamiltonian.
        """
        return EffectiveHamiltonian(
            rydberg=self.rydberg.discretize(device_capabilities)
        )


class Lattice(BaseModel):
    sites: List[Tuple[FloatType, FloatType]]
    filling: List[int]

    def __hash__(self):
        return hash((Lattice, tuple(self.sites), tuple(self.filling)))

    def discretize(self, device_capabilities: QuEraCapabilities):
        """
        Discretizes the lattice sites based on the task capabilities.

        Args:
           device_capabilities (QuEraCapabilities): Capabilities of the task for discretization.

        Returns:
           Lattice: Discretized lattice.
        """
        position_resolution = (
            device_capabilities.capabilities.lattice.geometry.position_resolution
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

    def discretize(self, device_capabilities: QuEraCapabilities):
        """
        Discretizes the task specification based on the task capabilities.

        Args:
           device_capabilities (QuEraCapabilities): Capabilities of the task for discretization.

        Returns:
           QuEraTaskSpecification: Discretized task specification.
        """
        return QuEraTaskSpecification(
            nshots=self.nshots,
            lattice=self.lattice.discretize(device_capabilities),
            effective_hamiltonian=self.effective_hamiltonian.discretize(
                device_capabilities
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
