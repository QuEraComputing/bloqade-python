This page is an excellent place to start for those familiar with the Neutral Atoms AHS model. For those who are not, we recommend you read our [Bloqade 101](bloqade_101.md) tutorial. Here, we will go through how to define your AHS program for two and three-level schemes. The beginning of your program starts with the atom geometry. You can build it as a list by or by using some pre-defined Bravais Lattices found in `bloqade.atom_arrangements`. For example, to define a simple 2x2 square lattice, you can do the following:

```python
from bloqade.atom_arrangements import Square

program = (
    Square(2, 2, lattice_spacing=6.0)
)
```
The analog pulse sequence is defined through the `.` syntax starting with which level coupling to drive `rydberg` or `hyperfine`. Next, specify the `detuning` and `rabi.amplitude` and `rabi.phase`. The `detuning` and `rabi.amplitude`. After this, you specify the spatial modulation of that waveform, e.g., the relative scale factor that each atom feels from a given waveform. Finally, you select the temporal modulation of the waveform. You can build the pulses in various ways. Because we use the `.` to split up the different parts of the pulse program, bloqade will only give you valid options for the next part of the pulse program. For example, to define a simple two-level rabi drive with a detuning:

```python
from bloqade import start

program = (
    start.add_position((0, 0))
    .rydberg.detuning.uniform.constant(10, 1.1)
    .amplitude.uniform.constant(15, 1.1)
)
```

There are some helpful shortcuts for generating piecewise linear and piecewise constant waveforms. For example, to define a piecewise linear rabi amplitude that starts at 0 ramps up to 15 rad/us, stays at 15 rad/us for 1.1 us, and then ramps back down to 0. The first list is the durations of each linear segment in us, and the second is the rabi amplitude in rad/us. The ith element in `durations` is the duration between `values[i]` and `values[i+1]`.

```python
from bloqade import start

program = (
    start.add_position((0, 0))
    .rydberg.detuning.uniform.constant(10, 1.1)
    .amplitude.uniform.piecewise_linear([0.05, 1.0, 0.05], [0, 15, 15, 0])
)
```

Note that because `rydberg.detuning` precedes `amplitude`, we do not need to specify `rabi.amplitude`. If we flip the order, we need to put `rabi` in the chain of dots. To run your program, you can select the backend you want to target:

```python
emulation_result = program.bloqade.python().run(100)
hardware_result = program.braket.aquila().run_async(100)
```
here, `run_async` denotes that the function call is asynchronous, meaning that the function will return immediately, and the result will be a future-like object that will handle retrieving the results from the cloud. You can also call `run`, but this will block Python until the results from the QPU have been completed. For more on this, see our [Tutorials](https://queracomputing.github.io/bloqade-python-examples/latest/).

It is easy to add hyperfine drives to your program. Select your program's `.hyperfine` property to start building the hyperfine pulse sequence. By selecting the `rydberg` and `hyperfine` properties, you can also switch back and forth between the different kinds of drives. To tell what kind of drive is being built, follow the string of options back to the first instance you find of either `rydberg` or `hyperfine`. Looking back also determines if the drive acts as the `detuning`, `rabi.amplitude`, and `rabi.phase`.

## Parameterized programs

This is very nice, but tracking individual tasks when doing parameter scans is annoying. Bloqade takes care of this by allowing you to parameterize the pulse sequences. For example, we want to sweep over the Rabi drive's drive time. In that case, you can insert strings into the fields to turn those into variables or make an explicit variable object:

```python
from bloqade import start, var

run_time = var("run_time")

program = (
    start.add_position((0, 0))
    .rydberg.detuning.uniform.constant(10, run_time + 0.1)
    .amplitude.uniform.piecewise_linear([0.05, run_time, 0.05], [0, 15, 15, 0])
)
```

here we use a variable `run_time`, which denotes the length of the rabi drive "plateau." These variables support `+`, `-`, `*`,  and`/`, as shown in the previous code example, which we used to define the duration of the detuning waveform in the last example code. To define a parameter scan, simply use the `batch_assign` method before calling the execution backend:

```python
result = (
    program.batch_assign(run_time=[0.1, 0.2, 0.3, 0.4, 0.5])
    .bloqade.python()
    .run(100)
)
```

There are also other methods available to assign the parameter; for example, if we do not know the values of the parameters we would like to run in a particular task, we can use the `args` method to specify that `"run_time"` will be assigned when calling the `run` or `run_async` methods. This function takes a list as an input, and the order of the names in the list corresponds to the order in the variables that need to be specified during the call of `run`. For example, let's say our program has two parameters, "a" and "b". We can specify both of these parameters as run time assigned:

```python
assigned_program = program.args(["a", "b"])
```
now when you execute this program you need to specify the values of "a" and "b" in the `run` method:

```python
result = assigned_program.bloqade.python().run(100, args=(1, 2))
```
where `args` argument is a tuple of the values of "a" and "b" respectively.

There is also an `assign(var1=value1, var2=value2, ...)` method which is useful if you are given a program that is imported from another package or comes from a source which you should not edit directly. In this case you can use the `assign` method to assign the value of the parameters for every task execution that happens.

## Analyzing results

### Batch Objects

Now that you have your program, we need to analyze the results. The results come in `RemoteBatch` and `LocalBatch`. `RemoteBatch` objects are returned from any execution that calls a remote backend, e.g. `braket.aquila()`. In contrast, `LocalBatch` is returned by local emulation backends, e.g., `bloqade.python()`, or `braket.local_emulator()`. The only difference between `RemoteBatch` and `LocalBatch` is that `RemoteBatch` has extra methods that you can use to fetch remote results, check the status of remote tasks, and filter based on the task status. Some things to note about `RemoteBatch` objects:

* Filtering is applied based on the tasks' _**current known status**_. If you filter based on the current status, you can precede the filter method with a `result.fetch()` call, e.g., `completed_results = results.fetch().get_completed_tasks()`.
* The `pull()` method will wait until all tasks have stopped running, e.g., tasks that are completed, failed, or canceled, before continuing execution of your Python code. This functionality is helpful for hybrid tasks where your classical step can only happen once the quantum task(s) have finished.

You must have active credentials for `fetch()` and `pull()` to run without an exception. Finally, batch objects can be saved/loaded as JSON via `bloqade.save`, `bloqade.dumps`, `bloqade.load`, `bloqade.loads`.

### Report Objects

Both `RemoteBatch` and `LocalBatch` objects support a `report()` method that will take any task data and package it up into a new object that is useful for various kinds of analysis. The three main modes of analysis are:

```python
report.bitstrings(filter_perfect_filling=True)
report.rydberg_densities(filter_perfect_filling=True)
report.counts(filter_perfect_filling=True)
```

During the program execution on the hardware, sometimes, atoms may not end up in every specified site; each shot is a pre and post-sequence measurement of the atoms. In specific applications, having a missing atom can mean your computation will not give the correct results, so it is helpful to filter out shots that are not perfectly filled using the boolean option in all three methods. Below, we summarize the different methods and what they return:

1. `bitstrings` is a method that returns a list of numpy arrays where each array is a (shots, num_sites) array of 0 or 1. Note that 0 corresponds to the Rydberg state while one corresponds to the ground state
2. `rydberg_densities` is a method that returns a Pandas Series object that is an average over the shots and gives the probability of each atom being in the rydberg state over every single task in the report.
3. `counts` is a method that returns a list of ordered dictionaries where the keys are the bitstrings as a string, and the values are the number of times that bitstring was observed in the shots.

Another helpful method is `report.list_param(param_string)`, which returns a list of values for the particular parameter given as a string in the function's input. This data is useful for plotting parameter scans. For example, if we want to plot the Rydberg density as a function of the Rabi drive time we can do the following:

```python
from bloqade import start
import matplotlib.pyplot as plt
import numpy as np

run_times = np.linspace(0,1,51)

report = (
    start.add_position((0, 0))
    .add_position((0, 5.0))
    .rydberg.detuning.uniform.constant(10, "run_time")
    .amplitude.uniform.constant(15, "run_time")
    .batch_assign(run_time=run_times)
    .bloqade.python().run(1000).report()
)

times = report.list_param("run_time")
densities = report.rydberg_densities(filter_perfect_filling=True)

plt.plot(times, densities)
plt.xlabel("Rabi Drive Time (us)")
plt.ylabel("Rydberg Density")
plt.show()
```

This concludes the intermediate tutorial, for more advanced usage see our [Advanced Usage](advanced_usage.md) tutorial.
