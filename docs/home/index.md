# Welcome to Bloqade -- QuEra's Neutral Atom SDK


## What is Bloqade?

Bloqade is an SDK designed to be a simple, easy-to-use interface for writing, submitting, and analyzing results of analog quantum programs on QuEra's neutral atom quantum computers. Currently, QuEra's hardware is on Amazon Braket, the primary method of accessing QuEra's quantum hardware. Over the alpha phase, we plan to expand the emulator capabilities to include a performance Python emulator but also a direct integration with Julia via [Bloqade.jl](https://queracomputing.github.io/Bloqade.jl/dev/).

## What does Bloqade do?

Bloqade is primarily a language for writing analog quantum programs for neutral atom quantum computers. Our interface is designed to guide our users through the process of defining a analog quantum program as well as different methods to run the program, whether it is on a real quantum computer or a simulator. Bloqade also provides a simple interface for analyzing the results of the program, whether it is a single run or a batch of runs or even some types of hybrid quantum-classical algorithms.

# How do I get started?

## Installation

You can install the latest version of Bloqade using pip:

```bash
pip install bloqade
```

## Your First Bloqade Program

If you are unfamiliar with Neutral Atom Analog Hamiltonian Simulation (AHS), we recommend you read our [Bloqade 101](bloqade_101.md) tutorial where we will give you a in depth introduction to AHS. If you are familiar with AHS, you can skip to the [Getting Started](getting_started.md) tutorial, and finally for more advanced usage of Bloqade you can read our [Advanced Usage](advanced_usage.md) tutorial.
