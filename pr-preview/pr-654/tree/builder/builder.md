
# Build workflow:

``` mermaid
graph TD

  ProgramStart(ProgramStart)

  Coupling["[Coupling]
  Rydberg , Hyperfine"]

  Detuning[Detuning]
  Rabi[Rabi]

  Amplitude[Amplitude]
  Phase[Phase]

  SpaceModulation(SpaceModulation)
  Waveform{Waveform}

  Options(["[Options]
  assign
  batch_assign
  args
  parallelize
  "])

  Services(["[Services]
  bloqade
  quera
  braket"])

  QuEraBackends(["[Backends]
  mock
  cloud_mock
  aquila
  device
  "])

  BraketBackends(["[Backends]
  aquila
  local_emulator
  "])

  BloqadeBackends(["[Backends]
  python
  julia
  "])

  Submit("[Submission]
  submit()
  run()
  __call__")

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
  QuEraBackends --> Submit;
  BraketBackends --> Submit;
  BloqadeBackends --> Submit;
```
