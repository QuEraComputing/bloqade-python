<div align="center">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/src/assets/logo-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="docs/src/assets/logo.png">
  <img alt="Bloqade Logo">
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

## Installation

You can install the package with `pip` in your Python environment of choice via:

```sh
pip install bloqade
```

## Documentation

If you're already convinced about what Bloqade brings to the table, feel free to take a look at our documentation with examples [here](https://queracomputing.github.io/bloqade-python/latest/). 

If you aren't convinced, keep scrolling!

## Features

### Smart Documentation

Get where you need to go in your program development with documentation that knows *where* and *when* it's needed. Never get lost developing your algorithm ever again! 

If you're a novice to neutral atoms, smart docs have your back. If you're an expert with neutral atoms, let smart docs give you some guidance on some new avenues for algorithm development.

![](docs/docs/assets/readme-gifs/smart-docs.gif)


### Fully Parameterized Analog Programs

*Parameter Sweeps* are a common element of programs for analog quantum computers where you want to observe differences in output from systematically varying value(s) in your program.

You used to have to manually keep track of all the small variations of your program per parameter, keeping careful track not to forget to submit one variation or lose one on top of a convoluted post-processing pipeline to incorporate all the results in one place.

Bloqade eliminates this with its own support for variables and internal handling of program parameter variations. Just drop in a variable in almost any place a single value can live and you can either assign a value later or a whole sequence of values to create a parameter sweep. 

Let Bloqade handle keeping track of all the variations while you focus on becoming a master of neutral atoms.

Did we mention you can throw your program at hardware and emulation and still keep your parameter sweeps?

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

### Integrated Visualization Tools

Simple and fast visualization for programs no matter how complex your program gets:

![](docs/docs/assets/readme-gifs/locations-hover.gif)
![](docs/docs/assets/readme-gifs/graph-select.gif)

The same holds for results: 

![](docs/docs/assets/readme-gifs/visualize-bitstrings.gif)
![](docs/docs/assets/readme-gifs/hover-bitstrings.gif)

### Maximum Composability

You can save any intermediate steps in your program construction, enabling you to build on top of a base program to produce all sorts of variants with ease.

Feel free to let your waveforms grow to your liking too!:

```python
from bloqade import start

# Save your intermediate steps any way you like
initial_geometry = start.add_position((0,0))
target_rabi_wf = initial_geometry.rydberg.rabi.amplitude.uniform
program_1 = target_rabi_wf.piecewise_linear(durations = [0.4, 2.1, 0.4], values = [0, 15.8, 15.8, 0])
# Tinker with new ideas in a snap
program_2 = target_rabi_wf.piecewise_linear(durations = [0.5, 1.0, 0.5], values = [0, 10.0, 11.0, 0]).constant(duration = 0.4, value = 5.1)

```

Want to focus on building one part of your program first before others (or, just want that same Bloqade.jl flavor?) We've got you covered:

```python
from bloqade import piecewise_linear
from bloqade.ir.location import Square

# Create a geometry without worrying about pulses yet
square_lattice = Square(3, "lattice_spacing")

# Develop your waveforms any way you like

adiabatic_durations = [0.8, 2.4, 0.8]
separate_rabi_amp_wf = piecewise_linear(durations = adiabatic_durations, values = [0.0, "max_rabi", "max_rabi", 0.0])

max_detuning = var("max_detuning")
separate_rabi_detuning = piecewise_linear(durations = adiabatic_durations, values = [-max_detuning, -max_detuning, max_detuning, max_detuning])

# Now bring it all together! 
# And why not sprinkle in some parameter sweeps for fun?
full_program = (
    square_lattice.rydberg.rabi.amplitude.uniform
    .apply(separate_rabi_amp_wf)
    .detuning.uniform
    .apply(separate_rabi_detuning)
    .assign(max_rabi = 15.8, 
            max_detuning = 16.33)
    .batch_assign(lattice_spacing = np.arange(4.0, 7.0, 0.5),
                  max_rabi = np.linspace(2 * np.pi * 0.5, 2 * np.pi * 2.5, 6))
)
```

### Efficient Atom Usage

Have an atom geometry that doesn't use up the entire FOV (Field of View) of the machine or all the possible qubits? Give `.parallelize` a spin!

If your geometry is compact enough, Bloqade can automatically duplicate/"tile" it in each shot with each copy separated by a distance of your specification to minimize interaction between copies. This lets you get more data per shot for more robust results.

Don't sweat the necessary post-processing of data for this, Bloqade does that for you and you can still preserve your standard post-processing pipelines:

```python
# you could just run your program and leave free qubits on the table...
program_with_few_atoms.braket.aquila().run_async(100)
# ...or you can take all you can get!
program_with_few_atoms.parallelize(24).braket.aquila(24).run_async(100)
```

### Contributing

Bloqade wouldn't exist if we weren't fortunate enough to obtain feedback from awesome members of our community such as yourself (:

If you find a bug, have an idea, or find an issue with our documentation, please feel free to file an issue on the [Github repo itself](https://github.com/QuEraComputing/bloqade-python/issues/new/choose). 

*May the van der Waals force be with you!*