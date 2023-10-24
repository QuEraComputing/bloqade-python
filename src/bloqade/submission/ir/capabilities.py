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


class RydbergCapabilities(BaseModel):
    c6_coefficient: Decimal
    global_: RydbergGlobalCapabilities
    local: RydbergLocalCapabilities

    class Config:
        allow_population_by_field_name = True
        fields = {"global_": "global"}


class LatticeGeometryCapabilities(BaseModel):
    spacing_radial_min: Decimal
    spacing_vertical_min: Decimal
    position_resolution: Decimal
    number_sites_max: int


class LatticeAreaCapabilities(BaseModel):
    width: Decimal
    height: Decimal


class LatticeCapabilities(BaseModel):
    number_qubits_max: int
    area: LatticeAreaCapabilities
    geometry: LatticeGeometryCapabilities


class TaskCapabilities(BaseModel):
    number_shots_min: int
    number_shots_max: int


class DeviceCapabilities(BaseModel):
    task: TaskCapabilities
    lattice: LatticeCapabilities
    rydberg: RydbergCapabilities


class QuEraCapabilities(BaseModel):
    version: str
    capabilities: DeviceCapabilities
