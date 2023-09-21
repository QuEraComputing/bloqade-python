
# Introducing Bloqade SDK for Python

![Bloqade Logo](../../../assets/logo.png#only-light)
![Bloqade Logo](../../../assets/logo-dark.png#only-dark)

Greetings Neutral Atom QC experts, enthusiasts, and newcomers!

We are ~~excited to the Rydberg state~~ thrilled to announce the Python version of our cutting-edge SDK, Bloqade. Originally developed in Julia, Bloqade has been a game-changer in the realm of Neutral Atom quantum computing. With the introduction of the Python version, we aim to make this revolutionary technology more accessible and user-friendly than ever before.


## Why Python?

Python is one of the most widely used programming languages, especially in the quantum computing community and broader scientific communities. By extending Bloqade to Python, we are opening doors to a broader audience, enabling more developers, researchers, and organizations to harness the power of Neutral Atom quantum computing.


## Neutral Atom Quantum Computing

Recently, the Neutral Atom platform has come on the QC scene in the form of Analog Hamiltonian Simulators that have a broad set of use cases beyond quantum circuits. Ranging from simulating unique quantum phases of matter, solving combinatorical optimization problems, and machine learning applications, the analog mode provides strong values in solving practical, interesting problems in the near term.

These advances are crucial milestones on the way towards scalable digital gate-based architecture using atom shuttling. This new technology and its novel applications demand a paradigm shift in the way we not only think about quantum computing, but translate those ideas to real hardware. Enter Bloqade, a next-generation SDK designed to put the power of neutral atoms at your fingertips.

## Why Bloqade?

Bloqade is designed with the primary goal of making it easier to compose programs for QuEra’s hardware and analyze results.

We've gained valuable insights into how users have used our neutral-atom hardware and with it, their struggles with existing tools. We took advantage of this knowledge to produce a tool that could take the "hard" out of "hardware". Bloqade is precision-balanced in both *flexibility* to empower novices to experiment with ease and *power* to let experts perform cutting-edge work without breaking a sweat.

### Highlights

#### Smart Documentation

With our commitment to enabling more seamless program development, we've put the relevant documentation you need right *where* and *when* you need it.

No more obnoxious switching between your favorite coding environment and documentation in a separate window. Let Bloqade guide you where you'd like to go:

![](../../assets/readme-gifs/smart-docs.gif)

#### Fully Parameterized Analog Programs

*Parameter sweeps* are a common theme of programs for analog quantum computers, where a user would like to observe differences in output results by varying a value or values in their program.

You used to have to manually crank out variations of your program with different values and then keep track of all the individual submissions to the emulator and hardware, a mess to keep track of and process the results of afterwards.

Bloqade eliminates this with its own support for variables that can later be assigned single values or a whole sequence of values for trivial parameter sweeping. This isn't some feature that's constrained to a certain backend, you can take your program with all its variables and submit it to your choice of emulator or our hardware directly.

```python
from bloqade import var
from bloqade.atom_arrangement import Square

import numpy as np

adiabatic_durations = [0.4, 3.2, 0.4]

# create variables explicitly...
max_detuning = var("max_detuning")
# ...or implicitly inside the program definition.
adiabatic_program = (
    Square(3, "lattice_spacing")
    .rydberg.rabi.amplitude.uniform.piecewise_linear(
        durations=adiabatic_durations, values=[0.0, "max_rabi", "max_rabi", 0.0]
    )
    .detuning.uniform.piecewise_linear(
        durations=adiabatic_durations,
        values=[
            -max_detuning, # scalar variables support direct arithmetic operations
            -max_detuning,
            max_detuning,
            max_detuning,
        ],
    )
    .assign(max_rabi=15.8, max_detuning=16.33)
    .batch_assign(lattice_spacing=np.arange(4.0, 7.0, 0.5))
)

# Launch your program on your choice of Braket or in-house emulator...
emu_results = adiabatic_program.braket.local_emulator().run(10000)
faster_emu_results = adiabatic_program.bloqade.python().run(10000)
# ...as well as hardware without stress
hw_results = adiabatic_program.parallelize(24).braket.aquila().run_async(100)

```

#### Integrated Visualization Tools

Instantly understand what your programs are doing faster than you can say "neutral atoms rock!" with Bloqade's built-in visualization tools:


![](../../../assets/readme-gifs/locations-hover.gif)

![](../../../assets/readme-gifs/graph-select.gif)


For your results, no more obnoxious manual compilation of results across different parameters or wrangling them into more useful forms. Get insights of experiment outcomes in the blink of an eye:

![](../../../assets/readme-gifs/visualize-bitstrings.gif)

![](../../../assets/readme-gifs/hover-bitstrings.gif)

Now that's what we call having your cake AND eating it.


## Bloqade Roadmap

### Bloqade Alpha Phase

During the next year, we plan on continuing development of Bloqade's python interface. If you are as excited about Neutral Atom quantum computing as us, or heck, even just quantum physics in general, give Bloqade a try! This is your opportunity to influence the direction of Bloqade and get in on the ground floor of the next Quantum Computing revolution.

### But what about Julia?

***Don't you guys already HAVE an SDK in Julia? Why do you need two SDKs?***


That's right! However, there's a key motivating factor for the reason we created Bloqade Python that's distinct for Bloqade.jl's existence.

Bloqade.jl is primarily geared as a *high-performance emulator*. It allows you to design complex neutral-atom algorithms that may not necessarily run on our hardware BUT are excellent if you're exploring novel physical phenonema/algorithms or as a tool for pedagogical purposes.

Bloqade.jl does have the ability to submit to [*Aquila*](https://www.quera.com/aquila), our flagship quantum computer, but for more complex tasks such as sweeping parameters (e.g. running the same program on hardware with slightly different parameters each time) or advanced post-processing, it becomes cumbersome quite quickly.

There are no plans to drop support any time soon though. On the contrary, we plan on fully integrating Bloqade.jl into the Python package, which will enable you to program Neutral Atom quantum hardware without having to choose.

We very much look forward to you trying out Bloqade!
