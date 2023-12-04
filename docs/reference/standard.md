
# Build Workflow
```mermaid

flowchart TD
  ProgramStart(["start"])

  Geometry("Geometry or Lattice")

  Coupling["Coupling
  -----------
  rydberg
  hyperfine"]

  Detuning["detuning"]
  Rabi["rabi"]

  Amplitude["amplitude"]
  Phase["phase"]

  SpaceModulation("SpatialModulation
  ----------------------
  uniform
  scale
  location
  ")
  Waveform{"Waveform
  ------------
  piecewise_linear
  piecewise_constant
  constant
  linear
  poly
  fn
  "}

  Options(["Options
  ---------
  assign
  batch_assign
  args
  parallelize
  "])

  Services(["Services
  ----------
  bloqade
  quera
  braket"])

  QuEraBackends(["Backends
  ------------
  mock
  cloud_mock
  aquila
  device"])

  BraketBackends(["Backends
  ------------
  aquila
  local_emulator"])

  BloqadeBackends(["Backends
  ------------
  python
  julia"])

  Execution("
  Execution hardware only
  -------------------------------
  run_async()

  Hardware and simulation
  -------------------------------
  run()
  __call__")

  ProgramStart -->|add_position| Geometry;
  Geometry --> Coupling;
  ProgramStart --> Coupling;

  Coupling --> Detuning;
  Coupling --> Rabi;

  Rabi --> Amplitude;
  Rabi --> Phase;

  Detuning --> SpaceModulation;
  Amplitude --> SpaceModulation;
  Phase --> SpaceModulation;

  SpaceModulation --> Waveform;

  Waveform --> Coupling;
  Waveform --> Services;
  Waveform --> Options;
  Options --> Services;

  Services -->|quera| QuEraBackends;
  Services -->|braket| BraketBackends;
  Services -->|bloqade| BloqadeBackends;
  QuEraBackends --> Execution;
  BraketBackends --> Execution;
  BloqadeBackends --> Execution;

  click ProgramStart "../bloqade/#bloqade.start";
  click Geometry "../bloqade/atom_arrangement/";
  click Coupling "../bloqade/builder/drive/";
  click Detuning "../bloqade/builder/field/#bloqade.builder.field.Detuning";
  click Rabi "../bloqade/builder/field/#bloqade.builder.field.Rabi";
  click Amplitude "../bloqade/builder/field/#bloqade.builder.field.Amplitude";
  click Phase "../bloqade/builder/field/#bloqade.builder.field.Phase";
  click SpaceModulation "../bloqade/builder/spatial/";
  click Waveform "../bloqade/builder/waveform/";
  click Options "../bloqade/builder/pragmas/";
  click Services "../bloqade/builder/backend/";
  click QuEraBackends "../bloqade/builder/backend/quera/#bloqade.builder.backend.quera.QuEraDeviceRoute";
  click BraketBackends "../bloqade/builder/backend/braket/#bloqade.builder.backend.braket.BraketDeviceRoute";
  click BloqadeBackends "../bloqade/builder/backend/bloqade/#bloqade.builder.backend.bloqade.BloqadeBackend";
  click Execution "../bloqade/ir/routine/braket/#bloqade.ir.routine.braket.BraketRoutine";

```
