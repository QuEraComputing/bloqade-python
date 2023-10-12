# Builder Overview

You may have noticed from the [Usage](../getting_started/philosophy.md) and [Tutorials](https://queracomputing.github.io/bloqade-python-examples/latest/)
that Bloqade uses this interesting, dot-intensive syntax.

```python
from bloqade import start

prog = start.add_position((0,0)).rydberg.rabi.amplitude.uniform.constant(1,1)
```
*Exhibit A: Lots of Dots*

In fact, it might look remniscent of what you see in some gate-based Quantum Computing SDKs:

```python
# this is strictly pseudocode
circuit = init_qubits(n_qubits)
# note the dots!
circuit.x(0).z(1).cnot(0, 1)...
```

What's the deal with that? 

## Syntax Motivations

We call this syntax the *builder* or *builder syntax* and as its name implies, it is designed to let you build programs for Analog Hamiltonian Simulation hardware as easily and as straightforward as possible.

The linear structure implies a natural hiearchy in how you think about targeting the various degrees of freedom (detuning, atom positions, Rabi amplitude, etc.) your program will have. In the beginning you have unrestricted access to all these degrees of freedom but in order to do something useful you need to:

1. Narrow down and explicitly identify **what** you want to control
2. Provide the instructions on **how** you want to control what your focused on

*Context* is a strong component of the builder syntax, as you are both actively restricted from doing certain things that can introduce ambiguity based on where you are in your program and repeating the same action in different parts of the program yields different results.

## Visual Guides

While we hope the Smart Documentation (the ability to instantly see all your next possible steps and their capabilities in your favorite IDE/IPython) is sufficient to get you where you need to go, we undestand it's particularly beneficial to get a high-level overview of things before diving in.

The [Standard Representation](standard.md) is a nice flow chart that gives a high-level overview of the different steps and components in the builder syntax.