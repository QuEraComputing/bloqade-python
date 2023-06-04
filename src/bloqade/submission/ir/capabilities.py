from pydantic import BaseModel

__all__ = ["QuEraCapabilities"]


class RydbergGlobalCapabilities(BaseModel):
    rabi_frequency_min: float
    rabi_frequency_max: float
    rabi_frequency_resolution: float
    rabi_frequency_slew_rate_max: float
    detuning_min: float
    detuning_max: float
    detuning_resolution: float
    detuning_slew_rate_max: float
    phase_min: float
    phase_max: float
    phase_resolution: float
    time_min: float
    time_max: float
    time_resolution: float
    time_delta_min: float


class RydbergLocalCapabilities(BaseModel):
    detuning_min: float
    detuning_max: float
    detuning_slew_rate_max: float
    site_coefficient_min: float
    site_coefficient_max: float
    number_local_detuning_sites: int
    spacing_radial_min: float
    time_resolution: float
    time_delta_min: float


class RydbergCapabilities(BaseModel):
    c6_coefficient: float
    global_: RydbergGlobalCapabilities
    local: RydbergLocalCapabilities

    class Config:
        allow_population_by_field_name = True
        fields = {"global_": "global"}


class LatticeGeometryCapabilities(BaseModel):
    spacing_radial_min: float
    spacing_vertical_min: float
    position_resolution: float
    number_sites_max: int


class LatticeAreaCapabilities(BaseModel):
    width: float
    height: float


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
