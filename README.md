# Welcome to Bloqade -- QuEra's Neutral Atom SDK

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

One can continue using the `.` to append more time dependent segments to the uniform detuning waveform, or one can select a different spatial modulation of the detuning field. The results will be that the new spatial modulation will be *added* to the existing spatial modulation. You can also start to build another field within the rydberg drive by selecting the `amplitude` or `phase` properties.

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
    .amplitude.uniform.
    piecewise_linear(
        durations = [0.1, 1.0 0.1],
        values = [0, 10, 10, 0]
    )
)
```

You can also go back to building the detuning field or even adding (e.g. waveform `+` waveform) to an existing spatial modulation of the detuning field by selecting the same spatial modulation property that was previously seen. You can also start to build the hyperfine drive by selecting the `hyperfine` property.

This is the general pattern, building under the context of a spatial modulation is appending to that waveform, while introducting a new or even the same spatial modulation will denote a new waveform to add to the exisiting waveform with that same spatial modulation.

Another option to remember is that each field that you input can be a literal value or a `str`. That string will not denote a variable that you can have in multiple parts of your program and when the variable is specified it will be the same throughout the entire program. For example if I would like to create a program parameterizing the final detuning value I could just inset a string for the final detuning value in the previously build program:

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
        values = [-10, -10, "final_detuning", "final_detuning"]
    )
    .amplitude.uniform.
    piecewise_linear(
        durations = [0.1, 1.0 0.1],
        values = [0, 10, 10, 0]
    )
)
```

Almost any field that is represented as a `Real` number if your program can be parameterized in this way. There are three ways to specify the run-time values for these parameters, the first is to specify the value via `assign` which means that the variable will have the same assignment regardless of the run. The second is to specify the value via `batch_assign` which assigns that parameter to a batch. When specifying a batch, the program will automatically execute a quantum teach for each paraeter in the batch. The other method to specify the variable is through `flatten`. This will delay the specification of the variable all the way till running/submitting the tasks. This is useful for certain kinds of hybrid quantum classical applications. This combined with the callable nature of the backends will make it very easy to create a quantum-classical loop. you can mix and match some of these methods and the availible options shuold pop up if you're using an IDE.

Another useful feature for small clusters of atoms is the `parallelize` option. The idea here is that for Aquila and other Nuetral Atom machines, the atoms are arranged in 2D space in some bounded square region. For small clusters of atoms you can effectively run multiple copies of that calculation in parallel by spacing those clusters apart by some sufficiently large distance. Our infrastructure will automatically detect the area of the QPU and use that to generate the appropriate number of copies of the calculation. Also when processing the results it is possible to automatically stitch the results from the different copies together so that the analysis is unified on the single cluster.

Now that we have specified all the different options we can now think about how to run our program. Currently we only supper `braket` which tells bloqade to submit your tasks to the braket service. The credentials are handled entirely by the braket SDK, so we suggest you look at their documentation for how to set that up, but the easiet way is to set up your AWS credentials in your environment variables. To execute the program on Aquila you simply select the `aquila` backend after `braket` proeprty.

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
        values = [-10, -10, "final_detuning", "final_detuning"]
    )
    .amplitude.uniform.
    piecewise_linear(
        durations = [0.1, 1.0 0.1],
        values = [0, 10, 10, 0]
    )
    .batch_assign(detuning_final=[0,1,2,3,4])
    .braket.aquila()
)
```
For tasks executed through a remote API there are three options to run your job. the first is an asynchronis call via `submit` which will return a `RemoteBatch` object. This object has various methods to `fetch` and or `pull` results from the remote API along with some other tools that can query the statis of the task(s) in this batch. The second option is to use the `run`, this also returns a `RemoteBatch` object but it will automatically wait for all the tasks in the batch to be completed before returning the object back to the user. The final option is to use the `__call__` method of the `calculation` object for hybrid workflows. The call method takes arguments specified in order specified by the `flatten` method during the options phase of the build. If no flatten method is called then the call method assumes no positional arguments, only some optional arguments via keyword. Calling this call method will also be blocking while waiting for the results to be retrieved. The `RemoteBatch` object can be saved in JSON format using the `save_batch` and reloaded back into python using the `load_batch` functions. This is useful for the asynchronous case where you can save the batch and then load it back in later to retrieve the results.

the braket service also provides a local emulator which can be run by selecting `local_emulator()` options after `braket` property. For local emulator jobs there is no asynchronous option, so you can only call `run` or `__call__` methods and the return results is a `LocalBatch`. The have a similar interface but the `LocalBatch` object have no method to `fetch` or `pull` resutls nor do they have any methods to query the status of the tasks. These results can also be serialized though for later use.

The batch objects can further be transformed into a `Report` object at any time. this object will contain all the data that is contained inside of the `Batch` object so if there are not results present in the `RemoteBatch`, then the `Report` will not have any data as well. A common pattern would be to first call `fetch` then create the `Report` by calling `report`, that way the generated report will have the most up-to-date results. Similarly if you are willing to wait you can call `pull` which will block until all tasks have stopped running.

Here is what a final calculation might look like for running a parameter scan anc comparing hardware to a classical emulator:

```python
from bloqade import start, save_batch

program = (
    start
    .add_position((0, 0))
    .add_position((0, 6.8))
    .add_positions([(6.8, 0), (6.8, 6.8)])
    .rydberg.detuning.uniform.
    piecewise_linear(
        durations = [0.1, 1.0, 0.1],
        values = [-10, -10, "final_detuning", "final_detuning"]
    )
    .amplitude.uniform.
    piecewise_linear(
        durations = [0.1, 1.0, 0.1],
        values = [0, 10, 10, 0]
    )
    .batch_assign(detuning_final=[0,1,2,3,4])
)

emulator_batch = program.braket.local_emulator().run(1000)

hardware_batch = program.parallelize(20).braket.aquila().submit(1000)

save_batch("emulator_results.json", emulator_batch)
save_batch("hardware_results.json", hardware_batch)

# Analysis script

from bloqade import load_batch

emulator_batch = load_batch("emulator_results.json")
hardware_batch = load_batch("hardware_results.json")

emulator_batch.report().show()
hardware_batch.fetch().report().show()

```

A good place to start for examples are the Aquila whitepaper examples bound [here]().


### Development Guide

If you want to setup locally for development, you can just cloning the repository and setup the
environment with [pdm](https://pdm.fming.dev/latest/).

```sh
pdm install

```

We also suggest you use our `pre-commit` hook to help you format your code.

```sh
pre-commit install
```
