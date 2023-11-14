
A basic AHS program contains two main parts: the __atom geometry__ and  __pulse sequence__. There are many ways to specify the atom Geometry, from a simple list of positions to Bravais lattices. The pulse sequence is defined as time-dependent functions for the detuning, Rabi amplitude, and Rabi phase for the driving between the energy levels of the atoms. Bloqade supports both two and three-level driving schemes. However, QuEra's flagship AHS device _Aquila_ only supports the two-level drive. Let's start by defining a simple two-level Rabi drive with a detuning:

```python
from bloqade import start

program = (
    start.add_position((0, 0))
    .rydberg.detuning.uniform.constant(10, 1.1)
    .amplitude.uniform.constant(15, 1.1)
)
```

The above code defines a single atom at the origin with a uniform detuning of 10 rad/us and a uniform Rabi amplitude of 15 rad/us for 1.1 us. With multiple atoms you can take advantage of _local_ detuning but we'll save that for the [Advanced Usage](advanced_usage.md) section.  The detuning and Rabi amplitude are both constant in time. You can execute this program on a simulator using the following code:

```python
result = program.bloqade.python().run(100)
```

Where the integer is the total number of shots to simulate. You cannot execute this code on the real hardware because the Rabi amplitude must start and end at 0. To do this, we need to add a ramp to the Rabi amplitude:

```python
from bloqade import start

program = (
    start.add_position((0, 0))
    .rydberg.detuning.uniform.constant(10, 1.1)
    .amplitude.uniform.piecewise_linear([0.05, 1.0, 0.05], [0, 15, 15, 0])
)
```

We can now run this program on actual hardware. After you obtain your Amazon Braket credentials through environment variables or the [AWS CLI](https://aws.amazon.com/cli/) we can use the `.run_async` method to submit to hardware.

```python
result = program.braket.aquila().run_async(100)
```

here, `run_async` denotes that the function call is asynchronous, meaning the function will return immediately, and the result will be a future-like object that will retrieve the results from the cloud. You can also call `run`, but this will block Python until the results from the QPU have been completed. For more information, see our [Tutorials](https://queracomputing.github.io/bloqade-python-examples/latest/). You can also execute your programs on the Amazon Braket local simulator using the following code:

```python
result = program.braket.local_emulator().run(100)
```

Note that the Amazon Braket local emulator doesn't have the same capabilities as the Bloqade local emulator (e.g. support for three-level simulations and better performance!)
