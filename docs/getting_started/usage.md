In bloqade we use the `.` to separate the different parts of your quantum program.  The reason for this is to guide you through how to build a neutral atom simulation. If you are using an IDE like PyCharm or VS code you can see the available options for building your program along with the documentation associated with each option. Similarly in Jupyter notebook environments you can also access this information via tab completion feature in Jupyter notebooks! That being said, we will go through a simple example of how to build a program in bloqade. We will start with a simple program that does nothing.

```python
from bloqade import start

calculation = (
    start
)

```

From here there will be different methods and properties that you can use to build your program. For example,
you can start to add atom sites to your program by selecting `add_position` method.

```python
from bloqade import start

calculation = (
    start
    .add_position((0, 0))
    .add_position((0, 6.8))
    .add_position([(6.8, 0), (6.8, 6.8)])
)
```

You can also start from a predefined geometry in the `bloqade.atom_arrangements` submodule. If you want to start to build the Rydberg drive you can select the `rydberg` property.

```python
from bloqade import start

calculation = (
    start
    .add_position((0, 0))
    .add_position((0, 6.8))
    .add_position([(6.8, 0), (6.8, 6.8)])
    .rydberg
)
```
Note that from here on out, you can no longer add to your geometry as the `rydberg` property is terminal. This is another advantage of using the `.` to separate the different parts of your program and guide you through the build process.

Continuing with our example, you can select the different parts of the Rydberg drive. For example, if you want to build the detuning part of the drive, you can choose the `detuning` property.

```python
from bloqade import start

calculation = (
    start
    .add_position((0, 0))
    .add_position((0, 6.8))
    .add_position([(6.8, 0), (6.8, 6.8)])
    .rydberg.detuning
)
```

In the code above, `rydberg.detuning` indicates that the following set of methods and properties will be related to the Detuning of the Rydberg drive. You can also select `rabi.amplitude` or `rabi.phase`
To build the amplitude and phase parts of the drive. Next, we will select the spatial modulation of the driving field.

```python
from bloqade import start

calculation = (
    start
    .add_position((0, 0))
    .add_position((0, 6.8))
    .add_position([(6.8, 0), (6.8, 6.8)])
    .rydberg.detuning.uniform
)
```

Here, we selected the `uniform` property, indicating that the detuning will be uniform across the atoms. You can also select `scale(value)` where `value` is a string to indicate a that you want to specify the value later or a list for the lattice site scaling. Having variables will allow you to define a spatially varying detuning as a list of real numbers. You can also select individual atoms using the `location(index, scale)` method, where `index` is the integer associated with the lattice. Now that we have the drive's spatial modulation, we can start to build the time dependence of the detuning field. Continuing with the example, we can add individual segments to the time function using `linear` or `constant` methods, or we have shortcuts to common waveforms like `piecewise_linear` or `piecewise_constant`. We use a piecewise linear function to define the Detuning waveform on Aquila.

```python
from bloqade import start

calculation = (
    start
    .add_position((0, 0))
    .add_position((0, 6.8))
    .add_position([(6.8, 0), (6.8, 6.8)])
    .rydberg.detuning.uniform
    .piecewise_linear(
        durations = [0.1, 1.0, 0.1],
        values = [-10, -10, 10, 10]
    )
)
```

One can continue using the `.` to append more time-dependent segments to the uniform detuning waveform or select a different spatial modulation of the detuning field. The results will be that the new spatial modulation will be *added* to the existing spatial modulation. You can also start to build another field within the Rydberg drive by selecting the `amplitude` or `phase` properties.

```python
from bloqade import start

calculation = (
    start
    .add_position((0, 0))
    .add_position((0, 6.8))
    .add_position([(6.8, 0), (6.8, 6.8)])
    .rydberg.detuning.uniform
    .piecewise_linear(
        durations = [0.1, 1.0, 0.1],
        values = [-10, -10, 10, 10]
    )
    .amplitude.uniform
    .piecewise_linear(
        durations = [0.1, 1.0, 0.1],
        values = [0, 10, 10, 0]
    )
)
```

If the next property is:
1. `hyperfine` will switch the build context to build the Hyperfine driving transition
2. `amplitude` or `rabi.amplitude` will start to build the rabi amplitude in the current context, e.g. rydberg
3. `phase` or `rabi.phase` will start to build the rabi phase in the current context e.g. rydberg
4. Selecting a new spatial modulation will add a new channel to the current field, e.g. detuning
5. Repeating the previously specified spatial modulations will add that waveform with the previously defined waveform in that spatial modulation.

```python
from bloqade import start

calculation = (
    start
    .add_position((0, 0))
    .add_position((0, 6.8))
    .add_position([(6.8, 0), (6.8, 6.8)])
    .rydberg.detuning.uniform
    .piecewise_linear(
        durations = [0.1, 1.0, 0.1],
        values = [-10, -10, "final_detuning", "final_detuning"]
    )
    .amplitude.uniform
    .piecewise_linear(
        durations = [0.1, 1.0, 0.1],
        values = [0, 10, 10, 0]
    )
)
```

A string can parameterize continuous values inside the program we call these run-time parameters. There are three ways to specify the value for these parameters; the first is to set the value via `assign`, which means that the variable will have the same assignment regardless of the run. The second is to specify the value via `batch_assign`, which assigns that parameter to a batch. When specifying a batch, the program will automatically execute a quantum teach for each parameter in the batch. The other method to define the variable is through `args`. This instruction will delay the specification of the variable till running/submitting the tasks, which is helpful for certain kinds of hybrid quantum-classical applications. Combined with the callable nature of the backends, it will make it very easy to create a quantum-classical loop. You can mix and match some of these methods, and the available options should pop up if you're using an IDE.

Another helpful feature for small clusters of atoms is the `parallelize` option. The idea here is that the atoms are arranged in 2D space in some bounded square region for Aquila and other Neutral Atom machines. You can run multiple copies of that calculation in parallel for small clusters of atoms by spacing those clusters apart by some sufficiently large distance. Our infrastructure will automatically detect the area of the QPU and use that to generate the appropriate number of copies of the calculation. Also, when processing the results, it is possible to automatically stitch the results from the different copies together so that the analysis is unified on the original cluster.

Now that we have specified all the options, we can think about how to run our program. We only support `braket`, which tells bloqade to submit your tasks to the braket service. The credentials are handled entirely by the braket SDK, so we suggest you look at their documentation for how to set that up. However, setting up your AWS credentials in your environment variables is the easiest way. To execute the program on Aquila, you select the `aquila` backend after the `braket` property.

```python
from bloqade import start

calculation = (
    start
    .add_position((0, 0))
    .add_position((0, 6.8))
    .add_position([(6.8, 0), (6.8, 6.8)])
    .rydberg.detuning.uniform
    .piecewise_linear(
        durations = [0.1, 1.0, 0.1],
        values = [-10, -10, "final_detuning", "final_detuning"]
    )
    .amplitude.uniform
    .piecewise_linear(
        durations = [0.1, 1.0, 0.1],
        values = [0, 10, 10, 0]
    )
    .batch_assign(final_detuning=[0,1,2,3,4])
    .braket.aquila()
)
```
For tasks executed through a remote API, there are three options to run your job. The first is an asynchronous call via `submit`, which will return a `RemoteBatch` object. This object has various methods to `fetch` and or `pull` results from the remote API, along with some other tools that can query the status of the task(s) in this batch. `run` is another method that blocks the script waiting for all the tasks to finish, subsequently returning the `RemoteBatch`. The final option is to use the `__call__` method of the `calculation` object for hybrid workflows. The call object is effectively the same as calling `run`. However, specifying the `args` option will allow you to call `__call__` with arguments corresponding to the list of strings provided by `args`.

The `RemoteBatch` object can be saved in JSON format using the `save` and reloaded back into Python using the `load` functions. This capability is useful for the asynchronous case, where you can save the batch and load it back later to retrieve the results.

The braket service also provides a local emulator, which can be run by selecting the `local_emulator()` options after the `braket` property. There is no asynchronous option for local emulator jobs, so you can only call `run` or `__call__` methods, and the return result is a `LocalBatch`.

The batch objects also have a method `report` that returns a `Report` object. This object will contain all the data inside the batch object, so if no results are present in the `RemoteBatch`, then the `Report` will not have any data either. A common pattern would be first to call `fetch` and then create the `Report` by calling `report`. That way, the generated report will have the most up-to-date results. Similarly, if you are willing to wait, you can call `pull`, which will block until all tasks have stopped running.

Here is what a final calculation might look like for running a parameter scan and comparing hardware to a classical emulator:

```python
from bloqade import start, save

program = (
    start
    .add_position((0, 0))
    .add_position((0, 6.8))
    .add_position([(6.8, 0), (6.8, 6.8)])
    .rydberg.detuning.uniform
    .piecewise_linear(
        durations = [0.1, 1.0, 0.1],
        values = [-10, -10, "final_detuning", "final_detuning"]
    )
    .amplitude.uniform
    .piecewise_linear(
        durations = [0.1, 1.0, 0.1],
        values = [0, 10, 10, 0]
    )
    .batch_assign(final_detuning=[0,1,2,3,4])
)

emulator_batch = program.bloqade.python().run(1000)

hardware_batch = program.parallelize(20).braket.aquila().submit(1000)

save(emulator_batch, "emulator_results.json")
save(hardware_batch, "hardware_results.json")

# Analysis script

from bloqade import load

emulator_batch = load("emulator_results.json")
hardware_batch = load("hardware_results.json")

emulator_batch.report().show()
hardware_batch.fetch().report().show()

```

An excellent place to start for examples is the Aquila whitepaper examples bound [here](). Also, a flow diagram can be found [here](../tree/builder.md) that discusses the entire build process.
