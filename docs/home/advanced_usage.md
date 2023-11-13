
## Geometry Concepts

In [Getting Started](getting_started.md) we discussed the parameterization of waveforms inside a rydberg/hyperfine drive. We have also provided infrastructure that allows you to parameterize the position of the atoms/sites in your atom array. There are a few methods to do this:

### Scaling Your Lattice

Every `AtomArrangement` object has an option to `scale` which applies a multiplication factor to all site coordinates. In order to parameterize this scaling you can either pass a literal value, a string or a scalar expression:

```python

new_geometry_1 = my_geometry.scale(1.0)
new_geometry_2 = my_geometry.scale('scale_factor')

scale_expr = var("param") / 2 + var("starting_scale")
new_geometry_3 = my_geometry.scale(scalar_expr)
```

### Parameterize the Position of a Individual Sites

if you are constructing a set of sites using the `start.add_position(...)` method, you can pass a literal value, a string or a scalar expression to the `position` argument:

```python

x_div_2 = var("x") / 2
y_dic_2 = var("y") / 2
start.add_position([(0, 1), ("x", "y"), (x_div_2, y_div_2)])
```

### Parallelize Over Space

For AHS programs with a small number of sites/atoms you can (and should) make full use of the user area allowed by QuEra's AHS devices. While the Rydberg interaction between the atoms decays as a power-law, it decays fast enough for you to cleanly separate small clusters of atom sites and be assured they will not interact and entangle with each other. This allows you to parallelize your program over space. We have added this functionality into Bloqade by simply calling the `.parallelize(spacing)` method, where `spacing` is a real value which is the spacing between the boudning boxes of the clusters. For example, if you have a 2x2 array of atoms and you want with a lattice spacing of 5 um,  calling `.parallelize(20.0)` would ensure that the atoms in other clusters are at least 20 um away from each other.

When fetching the results and generating the report the shot results will be organized by the cluster they belong. The methods of the `Report` object will always merge all the cluster shots together so you can analyze them as if you're analyzing the single cluster case.


## Programming A Local Drive

You might have noticed in the [Getting Started](getting_started.md) section that we used `...uniform...` when defining the various drives applied to the atoms. This is one special case of three total ways of defining the spatial modulation of the waveform. What do I mean by spacial modulation? In this case you think of a drive has having a temproal component, e.g. the Waveform, and a spatial component, which we call the spatial modulation. The spatial modulation is a scale factor that gets applied to the waveform when acting on a particular site. For example, if I have two atoms and I have a spatial modulation for site `0` is `0.1` and for site `1` is `0.2` then the waveform will be scaled by `0.1` when acting on site `0` and `0.2` when acting on site `1`.

Intuitively, `uniform` spatial modulation simply means that regardless of the atom, the waveform value is always the same. The other two options for defining spatial modulations are: `scale` and `location`. They have two distinct use cases:

## `scale` Method

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

## `location` Method

The `location` method takes two arguments with the second argument being optional. The first argument is an integer or a list of integers corresponding to the site(s) you want to apply the spatial modulation to. The second argument is the value you want to apply to the site(s). If you pass a list of integers then you must pass a list of values for the second argument. If you pass a single integer then you must a single value. The interpretation is that for any sites not specified in the first argument, the spatial modulation is `0.0`. Note that the values you pass in can be a real value, a string (for a variable), or a scalar expression. Below is an example using `location`:

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

In some cases you may want to run a program but at intermediate time points as a parameter scan. To facilitate this we have added the `slice` method that can be called during the construction of the waveform. The `slice` method takes two arguments: `start` and `stop`. For the `start` argument determines the new starting point for the sliced waveform while `stop` specifies the new stopping time for the waveform. A valid slice must have `start <= stop`, `start >= 0`, and `stop <= duration`, where `duration` is the duration of the waveform. Both arguments can be Scalar expressions as well as concrete values.

`record` is another useful feature we have implemented to be used with `slice`. For example, if you slice a waveform you may or may not know the value of the waveform at at the end of the resulting waveform from the slice. On the other hand, you need to be able create use that slice as a base for a new a waveform that is continuous, which requires knowledge of the value of the sliced waveform at the end of the slice. A common use case for this is to take a rabi drive and make sure that is `0` at the end of the protocol in order make it compatible with hardware. A great example of this exact use case is [Quantum Scar Dynamics Tutorial](https://queracomputing.github.io/bloqade-python-examples/latest/examples/example-4-quantum-scar-dynamics/) which goes through exactly how to use `slice` and `record` together.


## Python Functions as Waveforms

In Bloqade we provide a set of commonly used waveform shapes for hardware applications, however, we also allow users to pass a large variety of python functions as Waveforms! There are two ways to go about using python functions as waveforms. The first involves the passing the function in to the `fn()` method when building your program. The second involves the `bloqade.waveform` decorator on your function which will turn it into a `Waveform` object.

These are super connivent for emulation, however, these waveforms can't be directly implemented on quantum hardware. As such, we provide methods that make it easy to descretize your waveform in order into a form that is compatible with hardware. In general the easiest way to do this is to call the `sample` method. What this method does is replace your waveform into a piecewise linear or piecewise constant form. The Rabi amplitude and detuning both expect piecewise linear while the phase expects piecewise constant for the waveforms. If you are using the builder method you do not need to explicitly specify the kind of interpolation, it is deduced from the build, but if you are using the `waveform` decoration you need to specify the kind of interpolation, either `'linear'` or `'constant'`.

Example on [Floquet Dynamics](https://queracomputing.github.io/bloqade-python-examples/latest/examples/example-1-floquet/) is a good place to start with these particular features.
