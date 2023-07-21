
# Builder workflow:

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

  Codegen(["[Codegen]
  quera()
  mock()
  braket()
  braket_local_simulator()"])

  Submit("[Submission]
  submit()")

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
  Waveform --> Codegen;
  Codegen --> Submit;
```
