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

There are some helpful shortcuts for generating piecewise linear and piecewise constant waveforms. For example, to define a piecewise linear rabi amplitude that starts at 0, ramps up to 15 rad/us, stays at 15 rad/us for 1.1 us, and then ramps back down to 0. The first list is the durations of each linear segment in us and the second list is the rabi amplitude in rad/us. the ith element in `durations` is the duration between `values[i]` and `values[i+1]`.

```python
from bloqade import start

program = (
    start.add_position((0, 0))
    .rydberg.detuning.uniform.constant(10, 1.1)
    .amplitude.uniform.piecewise_linear([0.05, 1.0, 0.05], [0, 15, 15, 0])
)
```

Note that because `rydberg.detuning` preceeds `amplitude` we do not need to specify `rabi.amplitude` if flip the order we would need to put `rabi` in the chain of dots. To run your program you can simply select the backend you want to target:

```python
emulation_result = program.bloqade.python().run(100)
hardware_result = program.braket.aquila().run_async(100)
```
here `run_async` is used to denote that the function call is asynchronous. This means that the function will return immediately and the result will be a future like object that will handle retrieving the results from the cloud. you can also call `run` but this will block python until the results from the QPU have completed. For more on this see our [Tutorials](https://queracomputing.github.io/bloqade-python-examples/latest/).

It is easy to add hyperfine drives to your program. simply select the `.hyperfine` property of your program to start building the hyperfine pulse sequence. By selecting the `rydberg` and/or `hyperfine` properties you can swtich back and forth between the different kinds of drives as well. In order to tell what kind of drive is building built, follow the string of options back to the first instance you find of either `rydberg` or `hyperfine` and that will determine which transition is being driven for that part. Looking back also works for determining if the drive is acting as the `detuning`, `rabi.amplitude`, and `rabi.phase` as well.

## Parameterized programs

This is very nice but it is a bit annoying to have to keep take of individual tasks when doing parameter scans. For more rich programs you can also parameterize the pulse sequences for example, if we want to do a sweep over the drive time of the rabi drive you can simply insert strings into the fields to turn those into variables or make an explicit variable object:

```python
from bloqade import start, var

run_time = var("run_time")

program = (
    start.add_position((0, 0))
    .rydberg.detuning.uniform.constant(10, run_time + 0.1)
    .amplitude.uniform.piecewise_linear([0.05, run_time, 0.05], [0, 15, 15, 0])
)
```

here we use a variable `run_time` which denotes the length of the rabi drive "plateau". These variables support `+`,`-`,`*`,`/`, as show in the previous code example which we used to define the duration of the detuning waveform in the previous code example. To define a parameter scan simply use the `batch_assign` method before calling the execution backend:

```python
result = (
    program.batch_assign(run_time=[0.1, 0.2, 0.3, 0.4, 0.5])
    .bloqade.python()
    .run(100)
)
```

there are also other methods available to assign the parameters, for example, if we do not know the values of the parameters we would like to run in a particular task we can use the `args` method to specify that as a "run time" variable which is specified in the `run` method. this function takes a list as an input and the order of the names in the list correspond to the order the variables need to be specified in during the call of `run`. For example, lets say our program has two parameters, "a" and "b". We can specify both of these parameters as run time assigned:

```python
assigned_program = program.args(["a", "b"])
```
now when you execute this program you need to specify the values of "a" and "b" in the `run` method:

```python
result = assigned_program.bloqade.python().run(100, args=(1, 2))
```
where `args` argument is a tuple of the values of "a" and "b" respectively. There is also an `assign(var1=value1, var2=value2, ...)` method which is useful if you are given a program that is imported from another package or comes from a source which you should not edit directly. In this case you can use the `assign` method to assign the value of the parameters for every task execution that happens.

## Analyzing results

### Batch Objects

Now that you have your program we need to analyze the results. The results come on two forms, `RemoteBatch` and `LocalBatch`. `RemoteBatch` objects are returned from any execution that calls a remote backend, e.g. `braket.aquila()` while  `LocalBatch` is returned by local emulation backends, e.g. `bloqade.python()`, or `braket.local_emulator()`. The only difference between `RemoteBatch` and `LocalBatch` is that `RemoteBatch` has extra methods that you can use to fetch remote results, check of the status of remote tasks and filter based on the task status. Some things to note about `RemoteBatch` objects:

* Filtering is applied based on the _**current known status**_ of the tasks. If you filter based on the current status you can precede the filter method with a `result.fetch()` call, e.g. `completed_results = results.fetch().get_completed_tasks()`.
* The `pull()` method will wait until all tasks have stopped running, e.g. tasks that are completed, failed or canceled, before continuing execution of your python code. This is useful for hybrid tasks where your classical step can only happen once the quantum task(s) have completed.

Note that you must have active credentials for `fetch()` and `pull()` to work. Finally, batch objects can be saved/loaded as JSON via `bloqade.save`, `bloqade.dumps`, `bloqade.load`, `bloqade.loads`.

### Report Objects

Both `RemoteBatch` and `LocalBatch` objects support have a `report()` method will take any task data and package it up into a new object that is useful for various kinds of analysis. The three main modes of analysis are:

```python
report.bitstrings(filter_perfect_filling=True)
report.rydberg_densities(filter_perfect_filling=True)
report.counts(filter_perfect_filling=True)
```




This concludes the intermediate tutorial, for more advanced usage see our [Advanced Usage](advanced_usage.md) tutorial.
