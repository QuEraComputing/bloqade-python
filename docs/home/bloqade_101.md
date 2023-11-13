
A basic AHS program contains two main parts: First, the atom geometry, and second, the pulse sequence. There are many ways to specify the atom Geometry, from a simple list of positions to Bravais Lattices. The pulse sequence is defined as time-dependent functions for the detuning, rabi amplitude, and rabi phase for the driving between the energy levels of the atoms. Bloqade supports both two and three-level driving schemes. However, QuEra's flagship AHS device only supports the two-level drive. Let's start by defining a simple two-level rabi drive with a detuning:

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

where the integer is the total number of shots to simulate. You cannot execute this code on the hardware because the rabi amplitude must start and end at 0. To do this, we need to add a ramp to the rabi amplitude:

```python
result = program.braket.aquila().run_async(100)
```

here, `run_async` denotes that the function call is asynchronous, meaning the function will return immediately, and the result will be a future-like object that will retrieve the results from the cloud. You can also call `run`, but this will block Python until the results from the QPU have been completed. For more information, see our [Tutorials](https://queracomputing.github.io/bloqade-python-examples/latest/). You can also execute your programs on the braket local simulator using the following code:

```python
result = program.braket.local_emulator().run(100)
```

Note that the local emulator doesn't have the same capabilities as the Bloqade local emulator.
