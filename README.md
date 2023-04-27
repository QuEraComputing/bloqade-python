# Bloqade

The python SDK for Bloqade.

## Installation

If you want to setup locally for development, you can just cloning the repository and setup the
environment with [pdm](https://pdm.fming.dev/latest/).

```sh
poetry install
```

## Current Issues: The latency of the Python SDK is too large

Plan: remove DiffEq from our dependency and use our own solver
by copy pasting the code from DiffEq.

After removing DiffEq, the latency of python module seems to be
reasonable ~ 1.3s to load everything, roughly at the pytorch level.

Further latency optimization can be done in the future by caching
the compile result and trim the unnecessary native code. But for
now, the latency is acceptable.

## The Pulse language in Python

We tried to implement the pulse language in python by emulating
ADT using dataclass and python's pattern match. It is roughly
identical to the Julia implementation, thus should be relatively
easy to maintain.

The idea is to build the ADT nodes and user interface in Python,
and do more complicated anlaysis and simulation in Julia. We already
have a fairly complete Julia implementation of the pulse language.

## Integrations

### AWS Braket

- braket wants us to move visualization to a seprate package, which can be our `bloqade` package.

`braket-ahs-ext` should be supporting building pulse sequence from the Bloqade pulse language,
and then send the braket IR to our simulator. This would benefit both our python users and
braket users from all our future development on the Julia side.

- `bloqade`
  - `braket` via `braket-ahs-ext`
    - pure python module, interacts with braket
    - have the `ahs-ir` <-> `bloqade-ir` converter
    - this gets rid of the `julia` dependency for braket
  - `bloqade.visualizations`: pure python visualization code, might be adapted from `ahs-utils`
  - `bloqade.julia`: the Julia backend wrapper, contains corresponding type conversions.
  - `bloqade.ir`: the python objects for the pulse language.

### Difference between Python and Julia

- Julia is a replacement of C++ for the Python extension
- User interface is in Python
- Julia is developer oriented, unless we have open source
  contributions to improve the user interface.
- No simulation in Python

### Action Items

- [ ] Implement the pulse language in Python
- [ ] Remove DiffEq from the dependency in Julia
  - [ ] implement ODE solver
  - [ ] implement the pulse language to matrix codegen
- [ ] Implement the QuEra IR codegen
- [ ] Implement the braket IR codegen
