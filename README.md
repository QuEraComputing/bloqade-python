# Bloqade

The python SDK for Bloqade.

## Installation

You can install the package with pip.

```sh
pip install bloqade
```

## Usage philosophy

In bloqade we use the `.` to separate the different parts of your quantum program. The most basic starting point for your program will be 
the `bloqade.start` object. 

```python
from bloqade import start

calculation = (
    start
)

```

From here there will be different methods and properties that you can use to build your program. For example,
you can start to add atom sites to your program by selecting `add_position` method or `add_positions` method.

```python
from bloqade import start

calculation = (
    start
    .add_position((0, 0))
    .add_position((0, 6.8))
    .add_positions([(6.8, 0), (6.8, 6.8)])
)
```

If you want to start to build the Rydberg drive you can select the `rydberg` property.

```python
from bloqade import start

calculation = (
    start
    .add_position((0, 0))
    .add_position((0, 6.8))
    .add_positions([(6.8, 0), (6.8, 6.8)])
    .rydberg
)
```
Note that from here on out you can no longer add to your geometry as the `rydberg` property is a terminal property. 

From here you can select the different parts of the Rydberg drive. For example, if you want to build the detuning part of the drive you can select the `detuning` property.

```python
from bloqade import start

calculation = (
    start
    .add_position((0, 0))
    .add_position((0, 6.8))
    .add_positions([(6.8, 0), (6.8, 6.8)])
    .rydberg.detuning
)
```

This indicates that the follow set of methods and properties will be related to the `detuning` of the Rydberg drive. You can also select `rabi.amplitude` or `rabi.phase`
To build the amplitude and phase parts of the drive. Each driving field can be modulated spatially which is going to be the next set of options. 

```python
from bloqade import start

calculation = (
    start
    .add_position((0, 0))
    .add_position((0, 6.8))
    .add_positions([(6.8, 0), (6.8, 6.8)])
    .rydberg.detuning.uniform
)
```

Here we selected the `uniform` property which indicates that the detuning will be uniform across the atoms. You can also select `var(name)` where `name` is the name of the variable
defined using a string. This will allow you to define a spatially varying detuning which will be given as a list of real numbers. You can also select individual atoms using the `location(index)` method, where `index` is the integer associated with the lattice. Now that we have the spatial modulation of the drive we can start to build the time dependence of the detuning field. Continuing with the example we can add individual segments to the time function using `linear` or `constant` methods. or we have methods that are short cuts to common kinda of waveforms like `piecewise_linear` or `piecewise_constant`. On Aquila the detuning must be given in terms of piecewise linear.

```python
from bloqade import start

calculation = (
    start
    .add_position((0, 0))
    .add_position((0, 6.8))
    .add_positions([(6.8, 0), (6.8, 6.8)])
    .rydberg.detuning.uniform.
    piecewise_linear(
        durations = [0.1, 1.0 0.1],
        values = [-10, -10, 10, 10]
    )
)
```



### Development Guide

If you want to setup locally for development, you can just cloning the repository and setup the
environment with [pdm](https://pdm.fming.dev/latest/).

```sh
pdm install
```
