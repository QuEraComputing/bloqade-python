In [Getting Started](../getting_started.md) we discussed the parameterization of waveforms inside a rydberg/hyperfine drive. We have also provided infrastructure that allows you to parameterize the position of the atoms/sites in your atom array. There are a few methods to do this:

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
