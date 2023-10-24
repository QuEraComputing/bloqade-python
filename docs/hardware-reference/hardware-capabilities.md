# Hardware Capabilities

During program development, it can be quite handy to know what true hardware capabilities are and incorporate that information programmaticaly. Bloqade offers the ability to do this via `get_capabilities()`.

## Programmatic Access

`get_capabilities()` (importable directly from `bloqade`) returns a `QuEraCapabilities` object. This object contains all the hardware constraints in [`Decimal`](https://docs.python.org/3/library/decimal.html) format for the *Aquila* machine, our publically-accessible QPU on AWS Braket.

An example of using `get_capabilities()` is presented below:

```python
from bloqade import get_capabilities

# get capabilities for Aquila
aquila_capabilities = get_capabilities()

# obtain maximum Rabi frequency as Decimal
max_rabi = aquila_capabilities.rydberg.global_.rabi_freqeuncy_max

# use that value in constructing a neat Rabi waveform 
rabi_wf = piecewise_linear(durations = [0.5, 1.0, 0.5], values = [0, max_rabi, max_rabi, 0])
```

The attribute names for each value have been provided below but will require you to provide the proper prefix like in the example above (e.g. the maximum number of qubits lives under the `number_qubits_max` attribute which can be navigated to via `*your_QuEra_Capabilities_Object*.lattice.number_qubits_max`).


## *Aquila* Capabilities

### Task

* Use prefix `your_capabilities_object.capabilities.task` for:
    * minimum number of shots
    * maximum number of shots

| Capability              | Attribute          | Value |
|:------------------------|:-------------------|:------|
| Minimum Number of Shots | `number_shots_min` | 1     |
| Maximum Number of Shots | `number_shots_max` | 1000  |

### Lattice Geometry

* Use prefix `your_capabilities_object.capabilities.lattice` for:
    * maximum number of qubits
* Use prefix `your_capabilities_object.capabilities.lattice.area` for:
    * maximum lattice area width
    * maximum lattice area height
* Use prefix `your_capabilities_object.capabilities.lattice.geometry` for:
    * maximum number of sites
    * position resolution
    * minimum radial spacing
    * minimum vertical spacing

| Capability                              | Attribute              | Value   |
|:----------------------------------------|:-----------------------|:--------|
| Maximum Number of Qubits                | `number_qubits_max`    | 256     |
| Maximum Lattice Area Width              | `width`                | 75.0 µm |
| Maximum Lattice Area Height             | `height`               | 76.0 µm |
| Minimum Radial Spacing between Qubits   | `spacing_radial_min`   | 4.0 µm  |
| Minimum Vertical Spacing between Qubits | `spacing_vertical_min` | 4.0 µm  |
| Position Resolution                     | `position_resolution`  | 0.1 µm  |
| Maximum Number of Sites                 | `number_sites_max`     | 256     |

### Global Rydberg Values

* Use prefix `your_capabilities_object.capabilities.rydberg` for:
    * C6 Coefficient
* Use prefix `your_capabilities_object.capabilities.rydberg.global_` for:
    * Everything else related to global (applied to all atom) capabilities

| Capability                       | Attribute                      | Value                 |
|:---------------------------------|:-------------------------------|:----------------------|
| Rydberg Interaction Constant     | `c6_coefficient`               | 5.42×10⁶ rad/μs × µm⁶ |
| Minimum Rabi Frequency           | `rabi_frequency_min`           | 0.00 rad/μs           |
| Maximum Rabi Frequency           | `rabi_frequency_max`           | 15.8 rad/μs           |
| Rabi Frequency Resolution        | `rabi_frequency_resolution`    | 0.0004 rad/μs         |
| Maximum Rabi Frequency Slew Rate | `rabi_frequency_slew_rate_max` | 250.0 rad/µs²         |
| Minimum Detuning                 | `detuning_min`                 | -125.0 rad/μs         |
| Maximum Detuning                 | `detuning_max`                 | 125.0 rad/μs          |
| Detuning Resolution              | `detuning_resolution`          | 2.0×10⁻⁷ rad/μs       |
| Maximum Detuning Slew Rate       | `detuning_slew_rate_max`       | 2500.0 rad/µs²        |
| Minimum Phase                    | `phase_min`                    | -99.0 rad             |
| Maximum Phase                    | `phase_max`                    | 99.0 rad              |
| Phase Resolution                 | `phase_resolution`             | 5.0×10⁻⁷ rad          |
| Minimum Time                     | `time_min`                     | 0.0 µs                |
| Maximum Time                     | `time_max`                     | 4.0 µs                |
| Time Resolution                  | `time_resolution`              | 0.001 µs              |
| Minimum Δt                       | `time_delta_min`               | 0.05 µs               |

### Local Detuning Values

* Use prefix `your_capabilities_object.capabilities.rydberg.local` for the following values:

| Capability                             | Attribute                     | Value          |
|:---------------------------------------|:------------------------------|:---------------|
| Maximum Detuning                       | `detuning_max`                | 125.0 rad/μs   |
| Minimum Detuning                       | `detuning_min`                | 0 rad/μs       |
| Maximum Detuning Slew Rate             | `detuning_slew_rate_max`      | 1256.0 rad/µs² |
| Maximum Number of Local Detuning Sites | `number_local_detuning_sites` | 200            |
| Maximum Site Coefficient               | `site_coefficient_max`        | 1.0            |
| Minimum Site Coefficient               | `site_ceofficient_min`        | 0.0            |
| Minimum Radial Spacing                 | `spacing_radial_min`          | 5 µm           |
| Minimum Δt                             | `time_delta_min`              | 0.05 μs        |
| Time Resolution                        | `time_resolution`             | 0.001 µs       |