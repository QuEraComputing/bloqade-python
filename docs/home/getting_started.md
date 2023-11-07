
For those of you familiar with Neutral Atoms AHS model this is a good place to start. For those of you who are not, we recommend you read our [Bloqade 101](bloqade_101.md) tutorial. Here we will go through how to define your AHS program for two and three level schemes. The beginning of your program starts with the atom geometry. you can build it as a list by or by using some pre-defined Bravais Lattices found in `bloqade.atom_arrangements`. For example, to define a simple 2x2 square lattice you can do the following:

```python
from bloqade.atom_arrangements import Square

program = (
    Square(2, 2, lattice_spacing=6.0)
)
```
The analog pulse sequence is defined through the `.` syntax starting with which level coupling to drive `rydberg` or `hyperfine`. Next you specify the `detuning` and `rabi.amplitude` and `rabi.phase`. The `detuning` and `rabi.amplitude`. After this you specify the spatial modulation of that waveform, e.g. the relative scale factor that each atom feels from a given waveform. Finally, you specify the temporal modulation of the waveform. You can build the pulses in a variety of ways and because we use the `.` to split up the different parts of the pulse program bloqade will only give you valid options for the next part of the pulse program. For example, to define a simple two-level rabi drive with a detuning:

```python
from bloqade import start

program = (
    start.add_position((0, 0))
    .rydberg.detuning.uniform.constant(10, 1.1)
    .amplitude.uniform.constant(15, 1.1)
)
```

There are some helpful shortcuts for generating piecewise linear and piecewise constant waveforms. For example, to define a piecewise linear rabi amplitude that starts at 0, ramps up to 15 rad/us, stays at 15 rad/us for 1.1 us, and then ramps back down to 0. The first list is the time points in us and the second list is the rabi amplitude in rad/us.

```python
from bloqade import start

program = (
    start.add_position((0, 0))
    .rydberg.detuning.uniform.constant(10, 1.1)
    .amplitude.uniform.piecewise_linear([0.05, 1.0, 0.05], [0, 15, 15, 0])
)
```

Note that because `rydberg.detuning` preceeds `amplitude` we do not need to specify `rabi.amplitude` if flip the . To run your program you can simply select the backend you want to target:

```python
emulation_result = program.bloqade.python().run(100)
hardware_result = program.braket.aquila().run_async(100)
```
here `run_async` is used to denote that the function call is asynchronous. This means that the function will return immediately and the result will be a future like object that will handle retrieving the results from the cloud. you can also call `run` but this will block python until the results from the QPU have completed. For more on this see our [Tutorials](https://queracomputing.github.io/bloqade-python-examples/latest/). 

For more rich programs you can also parameterize the pulse sequences for example, if we want to do a parameter sweep over the drive time of the rabi drive you can simply insert strings into the fields to turn those into variables or make an explicit variable object:

```python
from bloqade import start, var

run_time = var("run_time")

program = (
    start.add_position((0, 0))
    .rydberg.detuning.uniform.constant(10, run_time + 0.1)
    .amplitude.uniform.piecewise_linear([0.05, run_time, 0.05], [0, 15, 15, 0])
)
```

