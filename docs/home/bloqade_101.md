

A basic AHS program contains two main parts: First, the atom geometry and second, the pulse sequence. There are many ways to specify tge atom Geometry from a simple list of positions to Bravais Lattices. The pulse sequence are defined as time dependent functions for the detuning, rabi amplitude and rabi phase for the driving between the energy levels of the atoms. Bloqade supports both two and three level driving schemes, however, QuEra's flagship AHS device only supports the two-level drive. Lets start out by defining a simple two-level rabi drive with a detuning:

```python
from bloqade import start

program = (
    start.add_position((0, 0))
    .rydberg.detuning.uniform.constant(10, 1.1)
    .amplitude.uniform.constant(15, 1.1)
)
```

The above code defines a single atom at the origin with a uniform detuning of 10 rad/us and a uniform rabi amplitude of 15 rad/us for 1.1 us. The detuning and rabi amplitude are both constant in time. You can execute this program on a simulator using the following code:

```python
result = program.bloqade.python().run(100)
```

where the integer is the total number of shots to simulate. You cannot execute this code on the real hardware because the rabi amplitude must start and end at 0. To do this, we need to add a ramp to the rabi amplitude:

```python
from bloqade import start

program = (
    start.add_position((0, 0))
    .rydberg.detuning.uniform.constant(10, 1.1)
    .amplitude.uniform.piecewise_linear([0.05, 1.0, 0.05], [0, 15, 15, 0])
)
```

The above code defines a piecewise linear rabi amplitude that starts at 0, ramps up to 15 rad/us, stays at 15 rad/us for 1.1 us, and then ramps back down to 0. The first list is the time points in us and the second list is the rabi amplitude in rad/us. You can execute this program on the real hardware through AWS Braket using the following code:

```python
result = program.braket.aquila().run_async(100)
```

here `run_async` is used to denote that the function call is asynchronous. This means that the function will return immediately and the result will be a future like object that will handle retrieving the results from the cloud. you can also call `run` but this will block python until the results from the QPU have completed. For more on this see our [Tutorials](https://queracomputing.github.io/bloqade-python-examples/latest/). You can also execute your programs on the braket local simulator using the following code:

```python
result = program.braket.local_emulator().run(100)
```

Note that the local emulator doesn't have the same capabilities of Bloqade local emulator. 

