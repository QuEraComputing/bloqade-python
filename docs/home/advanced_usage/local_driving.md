You might have noticed in the [Getting Started](../getting_started.md) section that we used `...uniform...` when defining the various drives applied to the atoms. This is one special case of three total ways of defining the spatial modulation of the waveform. What do I mean by spacial modulation? In this case you think of a drive has having a temproal component, e.g. the Waveform, and a spatial component, which we call the spatial modulation. The spatial modulation is a scale factor that gets applied to the waveform when acting on a particular site. For example, if I have two atoms and I have a spatial modulation for site `0` is `0.1` and for site `1` is `0.2` then the waveform will be scaled by `0.1` when acting on site `0` and `0.2` when acting on site `1`.

Intuitively, `uniform` spatial modulation simply means that regardless of the atom, the waveform value is always the same. The other two options for defining spatial modulations are: `scale` and `location`. They have two distinct use cases:

# `scale` Method

For the `scale` you can pass either a list of real values or a string. The list of values defines the scaling for every single atom in the system, so the number of elements must be equal to the number of sites in your geometry. the string is is a place-holder which allows you to define that mask as a list of values by passing them in through `assign`, `batch_assign`, or `args`. For `assign` and `batch_assign` you can simply past a list or a list of list respectively but with `args` is that the list of values must be inserted into the `args` tuple when calling `run` or `run_async`, for example lets take a two atom program:


```python
from bloqade import start

program = (
    start.add_position([(0, 0), (0, 5)])
    .rydberg.detuning.scale("local_detuning")
    .piecewise_linear([0.1, 1.0, 0.1], [0, "detuning", "detuning", 0])
    .amplitude.uniform.piecewise_linear([0.1, 1.0, 0.1], [0, 15, 15, 0])
    .args(["local_detuning", "detuning"])
    .bloqade.python()
)
```

in order to call the `run` method properly you must unpack the spatial modulation list into the tuple, e.g.

```python
local_detuning = [0.4, 0.1]

program.run(100, args=(*local_detuning, 30))
```

# `location` Method

The `location` method takes two arguments with the second argument being optional. The first argument is an integer or a list of integers corresponding to the site(s) you want to apply the spatial modulation to. The second argument is the value you want to apply to the site(s). If you pass a list of integers then you must pass a list of values for the second argument. If you pass a single integer then you must a single value. The interpretation is that for any sites not specified in the first argument, the spatial modulation is `0.0`. Note that the values you pass in can be a real value, a string (for a variable), or a scalar expression. Below is an example using `location`:

```python
program = (
    start.add_position([(0, 0), (0, 5)])
    .rydberg.detuning.location([0, 1], ["detuning_0", "detuning_1"])
    .piecewise_linear([0.1, 1.0, 0.1], [0, "detuning", "detuning", 0])
    .amplitude.location(0).piecewise_linear([0.1, 1.0, 0.1], [0, 15, 15, 0])
    .location(0,"rabi_scale").piecewise_linear([0.1, 1.0], [0, 15, 0])
)
```
