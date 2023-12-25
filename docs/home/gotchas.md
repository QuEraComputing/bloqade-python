# Bloqade *Gotchas*: Common Mistakes in Using Bloqade

It is tempting when coming from different quantum SDKs and frameworks to apply the same pattern of thought to Bloqade. However, a lot of practices from those prior tools end up being anti-patterns in Bloqade. While you can use those patterns and they can still work, it ends up causing you the developer to write unnecessarily verbose, complex, and hard-to-read code as well as preventing you from reaping the full benefits of what Bloqade has to offer.

This page is dedicated to cataloguing those anti-patterns and what you can do instead to maximize the benefit Bloqade can offer you.

## Redefining Lattices and Common Atom Arrangements

You might be tempted to define lattice-based geometries through the following means:

```python
from bloqade import start

spacing = 4.0
geometry = start.add_positions(
    [(i * spacing, j * spacing) for i in range(4) for j in range(4)]
)
```

This is quite redundant and verbose, especially considering Bloqade offers a large number of pre-defined lattices you can customize the spacing of in `bloqade.atom_arrangement`.
In the code above, we're just defining a 4x4 square lattice of atoms with 4.0 micrometers of spacing between them. This can be expressed as follows

```python
from bloqade.atom_arrangement import Square

spacing = 4.0
geometry = Square(4, lattice_spacing = spacing)
```


## Copying a Program to create New Ones

Many gate-based SDKs rely on having a mutable object representing your circuit. This means if you want to build on top of some base circuit without mutating it, you have to copy it:

```python
import copy

base_circuit = qubits.x(0)....
# make copy of base circuit
custom_circuit_1 = copy(base_circuit)
# build on top of copy of base circuit
custom_circuit_1.x(0).z(5)...
# create a new circuit by copying the base again
custom_circuit_2 = copy(base_circuit)
# build on top of that copy again
custom_circuit_2.y(5).cz(0,2)...
```

In Bloqade Python this is unnecessary because at every step of your program an immutable object is returned which means you can save it and not have to worry about mutating any internal state.

```python
from bloqade import start
base_program = start.add_position((0,0)).rydberg.rabi.amplitude.uniform
# Just recycle your base program! No `copy` needed!
new_program_1 = base_program.constant(duration=5.0, value=5.0)
new_program_2 = base_program.piecewise_linear(
    durations=[5.0], values = [0.0, 5.0]
)
```

## Creating New Programs Instead of Using `.batch_assign`

If you have a set of parameters you'd like to test your program on versus a single parameter, don't generate a new program for each value:

```python
rabi_values = [2.0, 4.7, 6.1]
programs_with_different_rabi_values = []

for rabi_value in rabi_values:
    program = start.add_position((0, 0)).rydberg.rabi.amplitude.uniform.constant(
        duration=5.0, value=rabi_value
    )
    programs_with_different_rabi_values.append(program)

results = []

for program in programs_with_different_rabi_values:
    result = program.bloqade.python().run(100)
    results.append(result)
```

Instead take advantage of the fact Bloqade has facilities *specifically designed* to make trying out multiple values in your program without needing to make individual copies via `.batch_assign`. The results are also automatically handled for you so each value you test has its own set of results, but all collected in a singular dataframe versus the above where you'd have to keep track of individual results.

```python
rabi_values = [2.0, 4.7, 6.1]
# place a variable for the Rabi Value and then batch assign values to it
program_with_rabi_values = start.add_position(
    0, 0
).rydberg.rabi.amplitude.uniform.constant(duration=5.0, value="rabi_value")
program_with_assignments = program_with_rabi_values.batch_assign(
    rabi_value=rabi_values
)

# get your results in one dataframe versus having to keep track of a
# bunch of individual programs and their individual results
batch = program_with_assignments.bloqade.python().run(100)
results_dataframe = batch.report().dataframe
```
