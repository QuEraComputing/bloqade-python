<div align="center">
<picture>
  <img id="logo_light_mode" src="assets/logo.png" alt="Bloqade Logo">
  <img id="logo_dark_mode" src="assets/logo-dark.png" alt="Bloqade Logo">
</picture>
</div>

[![Latest Version](https://img.shields.io/pypi/v/bloqade.svg)](https://pypi.python.org/pypi/bloqade)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/bloqade.svg)](https://pypi.python.org/pypi/bloqade)
[![codecov](https://codecov.io/github/QuEraComputing/bloqade-python/graph/badge.svg?token=4YJFc45Jyl)](https://codecov.io/github/QuEraComputing/bloqade-python)
![CI](https://github.com/QuEraComputing/bloqade-python/actions/workflows/ci.yml/badge.svg)
[![Documentation](https://img.shields.io/badge/Documentation-6437FF)](https://queracomputing.github.io/bloqade-python/latest/)

# Welcome to Bloqade -- QuEra's Neutral Atom SDK

## What is Bloqade?

Bloqade is an SDK designed to make writing and analyzing the results of analog quantum programs on QuEra's neutral atom quantum computers as seamless and flexible as possible. Currently, QuEra's hardware is on Amazon Braket, the primary method of accessing QuEra's quantum hardware. Over the alpha phase, we plan to expand the emulator capabilities to include a performance Python emulator but also a direct integration with Julia via [Bloqade.jl](https://queracomputing.github.io/Bloqade.jl/dev/).

## Why A Python Version of Bloqade?

Those coming from Bloqade.jl will most likely have this as their first question in mind. For newcomers the following information is still relevant.

Bloqade.jl was designed as an ***emulation-first*** SDK enabling users to investigate novel physical phenomena and develop complex algorithms with bleeding-edge performance. The result of this focus is that not everything made in Bloqade.jl is compatible with quantum hardware. While the ability to submit to Braket is available in Bloqade.jl it becomes cumbersome to analyze results and keep track of parameter sweeps.

In our mission to make neutral atom quantum computing more accessible to a broader community and the valuable feedback we've received in users of our quantum hardware, we took the opportunity to create a ***hardware-first*** SDK. One that is perfectly positioned to make it even easier to reap the benefits of neutral atoms while minimizing the pain points of initial program creation and post-processing results.

## What does Bloqade do?

Bloqade makes writing analog quantum programs for neutral atom quantum computers a cinch. Its interface is designed to make designing a program, analyzing its results, and building more complex algorithms as seamless as possible.

Our interface is designed to guide our users through the process of defining an analog quantum program as well as different methods to run the program, whether it be real quantum hardware or an emulator. Bloqade also provides a simple interface for analyzing the results of the program, whether it is a single run, a batch of runs, or even some types of hybrid quantum-classical algorithms.

## Getting Started

### Installation

You can install the package with `pip` in your Python environment of choice via:

```sh
pip install bloqade
```

## Developing your Bloqade Program

If you are unfamiliar with Neutral Atom Analog Hamiltonian Simulation (AHS), we recommend you read our [Bloqade 101](home/bloqade_101.md) tutorial where we will give you a in depth introduction to AHS. If you are familiar with AHS, you can skip to the [Getting Started](home/getting_started.md) tutorial, and finally for more advanced usage of Bloqade you can read our [Advanced Usage](home/advanced_usage.md) tutorial.
