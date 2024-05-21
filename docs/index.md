<div align="center">
<picture>
  <img id="logo_light_mode" src="assets/logo.png" style="width: 70%" alt="Bloqade Logo">
  <img id="logo_dark_mode" src="assets/logo-dark.png" style="width: 70%" alt="Bloqade Logo">
</picture>
</div>

[![Latest Version](https://img.shields.io/pypi/v/bloqade.svg)](https://pypi.python.org/pypi/bloqade)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/bloqade.svg)](https://pypi.python.org/pypi/bloqade)
[![codecov](https://codecov.io/github/QuEraComputing/bloqade-python/graph/badge.svg?token=4YJFc45Jyl)](https://codecov.io/github/QuEraComputing/bloqade-python)
![CI](https://github.com/QuEraComputing/bloqade-python/actions/workflows/ci.yml/badge.svg)

# **Welcome to Bloqade**: QuEra's Neutral Atom SDK

## What is Bloqade?

Bloqade is an open-source Python SDK created by [QuEra Computing Inc.](https://www.quera.com/) inspired by its Julia-based SDK [Bloqade.jl](https://queracomputing.github.io/Bloqade.jl/dev/). It's designed to make writing and analyzing the results of analog quantum programs on QuEra's Neutral Atom Quantum Computers as easy as possible. It allows you to define custom atom geometries and waveforms that enable fine control over the time evolution of a many-body neutral atom system in both emulation and real hardware. Bloqade interfaces with the [AWS Braket](https://aws.amazon.com/braket/) cloud service where QuEra's Quantum Computer *Aquila* is hosted, enabling you to submit programs as well as retrieve and analyze real hardware results with one tool.

## Installation

You can install the package with `pip` in your Python environment of choice via:

```sh
pip install bloqade
```

## A Glimpse of Bloqade

Let's try a simple example where we drive a [Rabi Oscillation](https://en.wikipedia.org/wiki/Rabi_cycle) on a single Neutral Atom. Don't worry if you're unfamiliar with the Many-Body Neutral Atom physics, (you can check out our Background for more information!) the goal here is to just give you a taste of what Bloqade can do.

We start by defining where our atoms go, otherwise known as the *atom geometry*. In this particular example we only need a single atom so we'll go ahead and just do the following:

```python
from bloqade import start

geometry = start.add_position((0,0))
```

We now define a waveform (part of our *pulse sequence*) for the time profile of the Rabi Drive targeting the Rydberg-Ground level transition, which causes the Rabi Oscillations. We choose a constant waveform with a value of pi/2 rad/us and a duration of 1.0 us.
This produces a pi/2 rotation on the Bloch Sphere meaning our final measurements should be split 50/50 between the ground and Rydberg state.

```python
from math import pi
rabi_program = geometry.rydberg.rabi.amplitude.uniform.constant(value=pi/2, duration=1.0)
```

We can now run the program through Bloqade's built-in emulator to get some results. We designate that we want the program to be run and measurements performed 100 times:

```python
emulation_results = rabi_program.bloqade.python().run(100)
```

With the results we can generate a report object that contains a number of methods for analyzing our data, including the number of counts per unique bitstring:

```python
bitstring_counts = emulation_results.report().counts()
```

Which gives us:

```
[OrderedDict([('0', 55), ('1', 45)])]
```

If we want to submit our program to hardware we'll need to adjust the waveform as there is a constraint the Rabi Amplitude waveform must start and end at zero. 
This is easy to do as we can build off the atom geometry we saved previously but apply a piecewise linear waveform;

```python
hardware_rabi_program = geometry.rydberg.rabi.amplitude.uniform.piecewise_linear(values = [0, pi/2, pi/2, 0], durations = [0.06, 1.0, 0.06])
```

Now instead of using the built-in Bloqade emulator we submit the program to the *Aquila* quantum computer hosted on Braket. You will need to use the [AWS CLI](https://aws.amazon.com/cli/) to obtain credentials from your AWS account 
or set the proper environment variables before hand. 

```python
hardware_results = hardware_rabi_program.braket.aquila.run_async(100)
```

`.run_async` is a non-blocking version of the standard `.run` method, allowing you to continue work while waiting for results from *Aquila*. `.run_async` immediately returns an object you can query for the status of your tasks in the queue as well.

You can do the exact same analysis you do on emulation results with hardware results too:

```python
hardware_bitstring_counts = hardware_results.report().counts()
```

## Features

### Customizable Atom Geometries 

You can easily explore a number of common geometric lattices with Bloqade's `atom_arrangement`'s:

```python
from bloqade.atom_arrangement import Lieb, Square, Chain, Kagome

geometry_1 = Lieb(3)
geometry_2 = Square(2)
geometry_3 = Chain(5)
geometry_4 = Kagome(3)
```

Or if you've got something more custom in mind, you can roll your own geometries out too:

```python
from bloqade import start

geometry = start.add_positions([(0,0), (6,0), (12,0)])
```

### Flexible Pulse Sequence Construction

Define waveforms for pulse sequences any way you like by either building (and chaining!) them immediately as part of your program:

```python
from bloqade.atom_arrangement import Square

geometry = Square(2)
target_rabi_amplitude = geometry.rydberg.rabi.amplitude.uniform
custom_rabi_amp_waveform = (
  target_rabi_amplitude
  .piecewise_linear(values=[0, 10, 10, 0], durations=[0.1, 3.5, 0.1])
  .piecewise_linear(values=[0, 5, 3, 0], durations=[0.2, 2.0, 0.2])
)
```

Or building them separately and applying them later:

```python
from bloqade.atom_arrangement import Square, Chain

geometry_1 = Square(3)
geometry_2 = Chain(5)

target_rabi_amplitude = start.rydberg.rabi.amplitude.uniform
pulse_sequence = target_rabi_amplitude.uniform.constant(value=2.0, duration=1.5).parse_sequence()

program_1 = geometry_1.apply(pulse_sequence)
program_2 = geometry_2.apply(pulse_sequence)
```

### Hardware and Emulation Backends

Go from a fast and powerful emulator:

```python
from bloqade.atom_arrangement import Square
from math import pi

geometry = Square(3, lattice_spacing = 6.5)
target_rabi_amplitude = geometry.rydberg.rabi.amplitude.uniform
program = target_rabi_amplitude.piecewise_linear(values = [0, pi/2, pi/2, 0], durations = [0.06, 1.0, 0.06])

emulation_results = program.bloqade.python().run(100)
```

To real quantum hardware in a snap:

```python
hardware_results = program.braket.aquila().run_async(100)
```

### Simple Parameter Sweeps

Use variables to make parameter sweeps easy on both emulation and hardware:

```python
from bloqade import start
import numpy as np

geometry = start.add_position((0,0))
target_rabi_amplitude = geometry.rydberg.rabi.amplitude.uniform
rabi_oscillation_program = target_rabi_amplitude.piecewise_linear(durations = [0.06, "run_time", 0.06], values = [0, 15, 15, 0])

rabi_oscillation_job = rabi_oscillation_program.batch_assign(run_time=np.linspace(0, 3, 101))

emulation_results = rabi_oscillation_job.bloqade.python().run(100)
hardware_results = rabi_oscillation_job.braket.aquila().run(100)
```

```
emulation_results.report().rydberg_densities()
                0
task_number      
0            0.16
1            0.35
2            0.59
3            0.78
4            0.96
...           ...
96           0.01
97           0.09
98           0.24
99           0.49
100          0.68

[101 rows x 1 columns]
```

### Fast Results Analysis

Want to just see some plots of your results? `.show()` will show you the way!

```python
from bloqade.atom_arrangement import Square

rabi_amplitude_values = [0.0, 15.8, 15.8, 0.0]
rabi_detuning_values = [-16.33, -16.33, 42.66, 42.66]
durations = [0.8, 2.4, 0.8]

geometry = Square(3, lattice_spacing=5.9)
rabi_amplitude_waveform = geometry.rydberg.rabi.amplitude.uniform.piecewise_linear(durations, rabi_amplitude_values)
program = rabi_amplitude_waveform.detuning.uniform.piecewise_linear(durations, rabi_detuning_values)

emulation_results = program.bloqade.python().run(100)
emulation_results.report().show()
```
![](/assets/index/report-visualization.png)

## Contributing to Bloqade

Bloqade is released under the [Apache License, Version 2.0](https://github.com/QuEraComputing/bloqade-python/blob/main/LICENSE). If you'd like the chance to shape the future of neutral atom quantum computation, see our [Contributing Guide](contributing/index.md) for more info!
