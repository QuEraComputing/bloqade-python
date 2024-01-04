from typing import Optional
from pydantic import BaseModel
from decimal import Decimal

__all__ = ["QuEraCapabilities"]


class RydbergGlobalCapabilities(BaseModel):
    rabi_frequency_min: Decimal
    rabi_frequency_max: Decimal
    rabi_frequency_resolution: Decimal
    rabi_frequency_slew_rate_max: Decimal
    detuning_min: Decimal
    detuning_max: Decimal
    detuning_resolution: Decimal
    detuning_slew_rate_max: Decimal
    phase_min: Decimal
    phase_max: Decimal
    phase_resolution: Decimal
    time_min: Decimal
    time_max: Decimal
    time_resolution: Decimal
    time_delta_min: Decimal

    def scale_units(
        self, _: Decimal, energy_scale: Decimal
    ) -> "RydbergGlobalCapabilities":
        return RydbergGlobalCapabilities(
            rabi_frequency_min=self.rabi_frequency_min * energy_scale,
            rabi_frequency_max=self.rabi_frequency_max * energy_scale,
            rabi_frequency_resolution=self.rabi_frequency_resolution * energy_scale,
            rabi_frequency_slew_rate_max=self.rabi_frequency_slew_rate_max
            * energy_scale**2,
            detuning_min=self.detuning_min * energy_scale,
            detuning_max=self.detuning_max * energy_scale,
            detuning_resolution=self.detuning_resolution * energy_scale,
            detuning_slew_rate_max=self.detuning_slew_rate_max * energy_scale**2,
            phase_min=self.phase_min,
            phase_max=self.phase_max,
            phase_resolution=self.phase_resolution,
            time_min=self.time_min / energy_scale,
            time_max=self.time_max / energy_scale,
            time_resolution=self.time_resolution / energy_scale,
            time_delta_min=self.time_delta_min / energy_scale,
        )


class RydbergLocalCapabilities(BaseModel):
    detuning_min: Decimal
    detuning_max: Decimal
    detuning_slew_rate_max: Decimal
    site_coefficient_min: Decimal
    site_coefficient_max: Decimal
    number_local_detuning_sites: int
    spacing_radial_min: Decimal
    time_resolution: Decimal
    time_delta_min: Decimal

    def scale_units(self, distance_scale, energy_scale) -> "RydbergLocalCapabilities":
        return RydbergLocalCapabilities(
            detuning_min=self.detuning_min * energy_scale,
            detuning_max=self.detuning_max * energy_scale,
            detuning_slew_rate_max=self.detuning_slew_rate_max * energy_scale**2,
            site_coefficient_min=self.site_coefficient_min * energy_scale,
            site_coefficient_max=self.site_coefficient_max * energy_scale,
            number_local_detuning_sites=self.number_local_detuning_sites,
            spacing_radial_min=self.spacing_radial_min * distance_scale,
            time_resolution=self.time_resolution / energy_scale,
            time_delta_min=self.time_delta_min / energy_scale,
        )


class RydbergCapabilities(BaseModel):
    c6_coefficient: Decimal
    global_: RydbergGlobalCapabilities
    local: Optional[RydbergLocalCapabilities]

    class Config:
        allow_population_by_field_name = True
        fields = {"global_": "global"}

    def scale_units(self, distance_scale, energy_scale) -> "RydbergCapabilities":
        return RydbergCapabilities(
            c6_coefficient=self.c6_coefficient * energy_scale * distance_scale**6,
            global_=self.global_.scale_units(distance_scale, energy_scale),
            local=self.local.scale_units(distance_scale, energy_scale),
        )


class LatticeGeometryCapabilities(BaseModel):
    spacing_radial_min: Decimal
    spacing_vertical_min: Decimal
    position_resolution: Decimal
    number_sites_max: int

    def scale_units(
        self, distance_scale: Decimal, _: Decimal
    ) -> "LatticeGeometryCapabilities":
        return LatticeGeometryCapabilities(
            spacing_radial_min=self.spacing_radial_min * distance_scale,
            spacing_vertical_min=self.spacing_vertical_min * distance_scale,
            position_resolution=self.position_resolution * distance_scale,
            number_sites_max=self.number_sites_max,
        )


class LatticeAreaCapabilities(BaseModel):
    width: Decimal
    height: Decimal

    def scale_units(
        self, distance_scale: Decimal, _: Decimal
    ) -> "LatticeAreaCapabilities":
        return LatticeAreaCapabilities(
            width=self.width * distance_scale,
            height=self.height * distance_scale,
        )


class LatticeCapabilities(BaseModel):
    number_qubits_max: int
    area: LatticeAreaCapabilities
    geometry: LatticeGeometryCapabilities

    def scale_units(
        self, distance_scale: Decimal, energy_scale: Decimal
    ) -> "LatticeCapabilities":
        return LatticeCapabilities(
            number_qubits_max=self.number_qubits_max,
            area=self.area.scale_units(distance_scale, energy_scale),
            geometry=self.geometry.scale_units(distance_scale, energy_scale),
        )


class TaskCapabilities(BaseModel):
    number_shots_min: int
    number_shots_max: int

    def scale_units(self, _: Decimal, __: Decimal) -> "TaskCapabilities":
        return TaskCapabilities(
            number_shots_min=self.number_shots_min,
            number_shots_max=self.number_shots_max,
        )


class DeviceCapabilities(BaseModel):
    task: TaskCapabilities
    lattice: LatticeCapabilities
    rydberg: RydbergCapabilities

    def scale_units(
        self, distance_scale: Decimal, energy_scale: Decimal
    ) -> "DeviceCapabilities":
        return DeviceCapabilities(
            task=self.task.scale_units(distance_scale, energy_scale),
            lattice=self.lattice.scale_units(distance_scale, energy_scale),
            rydberg=self.rydberg.scale_units(distance_scale, energy_scale),
        )


class QuEraCapabilities(BaseModel):
    version: str
    capabilities: DeviceCapabilities

    def scale_units(
        self, distance_scale: Decimal, energy_scale: Decimal
    ) -> "QuEraCapabilities":
        return QuEraCapabilities(
            version=self.version,
            capabilities=self.capabilities.scale_units(distance_scale, energy_scale),
        )
