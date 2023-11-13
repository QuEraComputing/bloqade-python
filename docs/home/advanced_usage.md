
## Geometry Concepts

In [Getting Started](getting_started.md), we discussed the parameterization of waveforms inside a Rydberg/hyperfine drive. We have also provided infrastructure that allows you to parameterize the position of the atoms/sites in your atom array. There are a few methods to do this:

### Scaling Your Lattice

Every `AtomArrangement` object has an option to `scale`, which applies a multiplication factor to all site coordinates. To parameterize this scaling, you can either pass a literal value, a string, or a scalar expression:

```python

new_geometry_1 = my_geometry.scale(1.0)
new_geometry_2 = my_geometry.scale('scale_factor')

scale_expr = var("param") / 2 + var("starting_scale")
new_geometry_3 = my_geometry.scale(scalar_expr)
```

### Parameterize the Position of a Individual Sites

Suppose you are constructing a set of sites using the `start.add_position(...)` method. In that case, you can pass a literal value, a string, or a scalar expression to the `position` argument:

```python

x_div_2 = var("x") / 2
y_dic_2 = var("y") / 2
start.add_position([(0, 1), ("x", "y"), (x_div_2, y_div_2)])
```

### Parallelize Over Space

For AHS programs with a few sites/atoms, you can (and should) make full use of the user area allowed by QuEra's AHS devices. While the Rydberg interaction between the atoms decays as a power-law, it decays fast enough for you to separate small clusters of atom sites cleanly and be assured they will not interact and entangle. This fact allows you to parallelize your program over space. We have added this functionality into Bloqade by simply calling the `.parallelize(spacing)` method, where `spacing` is a real value, the spacing between the bounding boxes of the clusters. For example,  calling `.parallelize(20.0)` would ensure that the atoms in other clusters are at least 20 um away from each other.

When fetching the results and generating the report, the shot results will be organized by the cluster to which they belong. The methods of the `Report` object will always merge all the cluster shots so you can analyze them as if you're analyzing a single cluster.


## Programming A Local Drive

In the [Getting Started](getting_started.md) section, you might have noticed that we used `...uniform...` when defining the various drives applied to the atoms. This syntax refers to one of three ways of expressing the spatial modulation of the waveform. What do I mean by spatial modulation? In this case, you think of a drive having a temporal component, e.g., the waveform, and a spatial part, which we call spatial modulation. The spatial modulation is a scale factor applied to the waveform when acting on a particular site. For example, if I have two atoms and I have a spatial modulation for site-`0` is `0.1` and for site-`1` is `0.2`, then the waveform will be scaled by `0.1` when acting on-site `0` and `0.2` when applied to site-`1`.

Intuitively, `uniform` spatial modulation simply means that regardless of the atom, the waveform value is always the same. The other two options for defining spatial modulations are: `scale` and `location`. They have two distinct use cases:

## `scale` Method

When calling the 'scale ' method, you can pass either a list of real values or a string. The list of values defines the scaling for every atom in the system, so the number of elements must equal the number of sites in your geometry. The string is a placeholder that allows you to define that mask as a list of values by passing them in through `assign`, `batch_assign`, or `args`. For `assign` and `batch_assign`, you can pass a list or a list of lists, respectively. On the other hand, `args`, the list of values, must be inserted into the `args` tuple when calling `run` or `run_async`, for example, let's take a two-atom program:


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

To call the `run` method properly, you must unpack the spatial modulation list into the tuple, e.g.

```python
local_detuning = [0.4, 0.1]

program.run(100, args=(*local_detuning, 30))
```

## `location` Method

The `location` method takes two arguments; the second is optional. The first argument is an integer or a list of integers corresponding to the site(s) to which you want to apply the spatial modulation. The second argument is the value you wish to apply to the site(s). If you pass a list of integers, you must pass a list of values for the second argument, while if you pass a single integer, you must pass a single value. The interpretation is that for any sites not specified in the first argument, the spatial modulation is `0.0`. Note that the values you pass in can be a real value, a string (for a variable), or a scalar expression. Below is an example using `location`:

```python
program = (
    start.add_position([(0, 0), (0, 5)])
    .rydberg.detuning.location([0, 1], ["detuning_0", "detuning_1"])
    .piecewise_linear([0.1, 1.0, 0.1], [0, "detuning", "detuning", 0])
    .amplitude.location(0)
    .piecewise_linear([0.1, 1.0, 0.1], [0, 15, 15, 0])
    .location(0, "rabi_scale")
    .piecewise_linear([0.1, 1.0], [0, 15, 0])
)
```

## Slicing Waveforms

Sometimes, you want to run a program at intermediate time points as a parameter scan. To facilitate this, we have added the `slice` method that can be called during the waveform construction. The `slice` method takes two arguments: `start` and `stop`. The `start` argument determines the new starting point for the sliced waveform. At the same time, `stop` specifies the new stopping time for the waveform. A valid slice must have `start <= stop`, `start >= 0`, and `stop <= duration`, where `duration` is the duration of the waveform. Both arguments can be Scalar expressions as well as concrete values.

`record` is another useful feature we have implemented to be used with `slice`. For example, if you slice a waveform, you may or may not know the value of the waveform at the end of the resulting waveform from the slice. On the other hand, you need to be able to use that slice as a base for a new waveform that is continuous, which requires knowledge of the value of the sliced waveform at the end of the slice. A common use case for this is to take a Rabi drive and ensure it is `0` at the end of the protocol to make it compatible with hardware. A great example of this exact use case is [Quantum Scar Dynamics Tutorial](https://queracomputing.github.io/bloqade-python-examples/latest/examples/example-4-quantum-scar-dynamics/), which goes through exactly how to use `slice` and `record` together.


## Python Functions as Waveforms

In Bloqade, we provide a set of commonly used waveform shapes for hardware applications. However, we also allow users to pass various Python functions as Waveforms! There are two ways to go about using Python functions as waveforms. The first involves passing the function into the `fn()` method when building your program. The second involves the `bloqade.waveform` decorator on your function, turning it into a `waveform` object.

These are super convenient for emulation. However, these waveforms can't be executed on quantum hardware. As such, we provide the `sample` method that allows you to easily discretize your waveform into a form compatible with the hardware. This method replaces your waveform with a piecewise linear or piecewise constant form. The Rabi amplitude and detuning both expect piecewise linear while the phase expects piecewise constant for the waveforms. If you are using the builder method to build your program, you do not need to specify the kind of interpolation explicitly;  Bloqade can deduce from the build what type of interpolation to do, but if you are using the `waveform` decoration, you need to specify the kind of interpolation, either `'linear'` or `'constant'`.

An example on [Floquet Dynamics](https://queracomputing.github.io/bloqade-python-examples/latest/examples/example-1-floquet/) is an excellent place to start with these particular features.
