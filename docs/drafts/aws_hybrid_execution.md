# Hybrid Execution with AWS Hybrid Jobs

## Introduction

Analog Hamiltonian Simulation (AHS) has proven itself to be a powerful method of performing quantum computation that is well-suited for solving optimization problems and performing computationally difficult simulations of other quantum systems. Unlike its counterpart digital/gate-based quantum computing where you think of your programs in terms of unitary operations that are akin to classicla gates, you think of programs in AHS in terms of the geometry of your qubits (individual atoms!) and the waveforms of the lasers that are applied to them.

The team at QuEra Computing believes this is a useful step in the path to fault tolerant quantum computation but also realizes that such novel power and capabilities require a novel tool.

That's why we're proud to announce the release of the Bloqade SDK for Python! We've had the opportunity to obtain valuable feedback from the community and leveraged our unique position as the only provider of publicly cloud-accessible Nuetral Atom hardware to produce a tool that puts the power of AHS hardware at your fingertips.

## Installation

Bloqade is a pure Python library so installation is as easy as `pip install bloqade`! Once installed you have a variety of options for building your Nuetral atom Analog program. We have worked very hard to provide a seamless user experience when venturing into unfamiliar territory of AHS with Nuetral Atoms! Let’s dig into some of the major features Bloqade has to offer!

## Features of Bloqade

### Just-in-time Documentation

I know you have probably spent a pretty penny on your multi-monitor setup so that you do not have to switch between windows when writing code and looking at documentation. What if I told you there was a better way? What if your code contained all the documentation you needed to continue writing your program? That’s exactly what we have designed in the user experinence (UX) of Bloqade.

Typically when building an AHS program one needs to construct many different objects and combine them in very particular ways which are not obvious without understanding the concept as a whole. Bloqade provides a unique experience programming AHS. Our interface eases the user into AHS programming by using Python’s rich type-hinting system.  Most IDE's, as well as IPython and Jupyter, use the type hints to access to the methods and attributes that are availible to whatever object you currently have. We use this hinting to our advantage in Bloqade by building your AHS program with a chain of methods and attributes separated by `.`. In doing so you will be given hints as to what to do next at every step of the way when building your program.

![](https://hackmd.io/_uploads/rJnd8rNMT.gif)


While it is conventional thinking that it is bad to chain `.` statements together, there are some well known libraries like [Pandas](https://medium.com/@ulriktpedersen/modern-pandas-streamlining-your-workflow-with-method-chaining-f65e75deb193) that can and do make heavy use of this pattern of programming. The dot-chaining syntax also integrate python linters like [black](https://github.com/psf/black) to make your code highly readable without having to do anything other can call the linter on your python file.

Example, before linter some unstrctured code
![](https://hackmd.io/_uploads/Hk_t1BVfT.png)
After running black we get consistent formatting.
![](https://hackmd.io/_uploads/rkbckHNMp.png)
In this case properties are always chained which makes reading the code a lot like reading a sentence.

On top of these nice features, If you’re in an IDE like VS code or PyCharm you can access the documentation of each method and attribute in which we provide even more hints for the next step after your current selection

![](https://github.com/QuEraComputing/bloqade-python/blob/main/docs/assets/readme-gifs/smart-docs.gif?raw=True)


[Here](https://towardsdatascience.com/the-unreasonable-effectiveness-of-method-chaining-in-pandas-15c2109e3c69) is a blog post that goes into the advantages and disadvantages of chaining method calls/attributes like we have shown. It worth a read if you are still a bit skeptical! It's worth noting that you do not neccesarily have to chain method/attribute calls you can safely store a intermediate parts of program with intermediate objects because calling a method *does not* act in the object in-place. This means you can

## Parameterized Programs
> keep title capitalization consistent [name=jzlong]

Many near-term applications for QC as well as AHS require some notion of parameterized programs. We’ve made this a first-class feature in Bloqade enabling you to write a single AHS program precisely to define your experiment or algorithm symbolically enabling more readable and sharable code!

You can also create stand-alone variables which have a basic symbolic representation that support some arithmetic operations that are useful for more advanced AHS applications. For example, say I have a piecewise linear pulse that has variable segments but I have another constant waveform running for the total time of the other waveform. I can sum the durations of each segment of the piecewise linear waveform to get the total duration and use that to construct the constant waveform.

```python
from bloqade import var, start

rabi_durations = [0.1, var("run_time"), 0.1]
total_time = sum(rabi_durations)

program = (
    start.add_position((0, 0))
    .rydberg.detuning.uniform.constant(total_time, "detuning")
    .amplitude.uniform.piecewise_linear(
        rabi_durations, [0, "amplitude",  "amplitude",  0]
    )
)
```

Once you have defined your parameterized program there are three different methods of specifying the run time values of the parameters:

```python
program.assign(var1=value1, var2=value2)
```

which assigns the variables in a static way. The basic logic here is for segments of program in which you want to share without limiting other users to use the concrete values you decided works for you.

```python
program.batch_assign(var1=[value1_1, value1_2, …],…)
```
or

```python
program.batch_assign([dict(var1=value1_1,…), dict(var1=value1_2,…),…])
```

specify a batch of tasks via parameters assigned to lists or a list of dictionaries with the assigned parameters. Next,

```python
args([“var1”, “var2”])
```

will delay the assignment of the variable until the program is being executed. We will discuss this below in more detail.

Note that none of these methods are required for non-parameterized programs. For parameterized programs you can mix and match all of these assignments together. However, they will always come in the order of `assign`, `batch_assign` then `args`. let's take the program above to give a concrete example.

After specifying the program we can do the following assignment:

```python
assigned_program = (
    program.assign(amplitude=15.7)
    .batch_assign(run_time=np.linspace(0.05, 3.0, 101))
    .args(["detuning"])
)
```

First we assign the amplitude to a value of 15.7 which is going to be non-changing regardless of the other changing parameters in execution. Because we assign ‘run_time’ using `batch_assign` that means every time we execute this program we will run 101 tasks with the parameter sweep defined by the list of values. Finally `args([“detuning”])` implies that you must provide the value of the detuning as an argument when calling the execution method of the device. This is primarily useful for hybrid work flows or if you are simply just wanting to split your experiments into chunks defined by a different set of parameters. In conclusion, whether it is a hybrid algorithm or a parameter scan for your next fancy experiment Bloqade has you covered!

### Visualization Tools

While having a clean, readable syntax is great, there is always going to be the need for more visual representations. This is especially true for AHS programming where you think about things in terms of waveforms and atom configurations. As such, we provide visualization of your programs using `Bokeh`. Bokeh allows for very clean responsive interactive plots which we have implemented not only for AHS programs but AHS results as well!


![](https://github.com/QuEraComputing/bloqade-python/blob/main/docs/assets/readme-gifs/locations-hover.gif?raw=true)

![](https://github.com/QuEraComputing/bloqade-python/blob/main/docs/assets/readme-gifs/graph-select.gif?raw=true)

We also provide some visualization of your AHS program in the terminal:

```ipython
In [1]: from bloqade import start
   ...:
   ...: program = (
   ...:     start.add_position((0, 0))
   ...:     .add_position((0, "r"))
   ...:     .rydberg.detuning.uniform.piecewise_linear([0.1, 1.2, 0.1], [-20, -20, 20, 20])
   ...:     .amplitude.uniform.piecewise_linear([0.1, 1.2, 0.1], [0, 15, 15, 0])
   ...:     .args(["r"])
   ...: )

In [2]: program.parse_circuit()
Out[2]:
AnalogCircuit
├─ register
│  ⇒ AtomArrangement
│    ├─ Location: filled
│    │  ├─ x
│    │  │  ⇒ Literal: 0
│    │  └─ y
│    │     ⇒ Literal: 0
│    └─ Location: filled
│       ├─ x
│       │  ⇒ Literal: 0
│       └─ y
│          ⇒ Variable: r
└─ sequence
   ⇒ Sequence
     └─ RydbergLevelCoupling
        ⇒ Pulse
          ├─ Detuning
          │  ⇒ Field
          │    └─ Drive
          │       ├─ modulation
          │       │  ⇒ UniformModulation
          │       └─ waveform
          │          ⇒ Append
          │            ├─ Linear
          │            │  ├─ start
          │            │  │  ⇒ Literal: -20
          │            │  ├─ stop
          │            │  │  ⇒ Literal: -20
          │            │  └─ duration
          │            │     ⇒ Literal: 0.1
          │            ├─ Linear
          │            │  ├─ start
          │            │  │  ⇒ Literal: -20
          │            │  ├─ stop
          │            │  │  ⇒ Literal: 20
          │            │  └─ duration
          │            │     ⇒ Literal: 1.2
          │            └─ Linear
          │               ├─ start
          │               │  ⇒ Literal: 20
          │               ├─ stop
          │               │  ⇒ Literal: 20
          │               └─ duration
          │                  ⇒ Literal: 0.1
          └─ RabiFrequencyAmplitude
             ⇒ Field
               └─ Drive
                  ├─ modulation
                  │  ⇒ UniformModulation
                  └─ waveform
                     ⇒ Append
                       ├─ Linear
                       │  ├─ start
                       │  │  ⇒ Literal: 0
                       │  ├─ stop
                       │  │  ⇒ Literal: 15
                       │  └─ duration
                       │     ⇒ Literal: 0.1
                       ├─ Linear
                       │  ├─ start
                       │  │  ⇒ Literal: 15
                       │  ├─ stop
                       │  │  ⇒ Literal: 15
                       │  └─ duration
                       │     ⇒ Literal: 1.2
                       └─ Linear
                          ├─ start
                          │  ⇒ Literal: 15
                          ├─ stop
                          │  ⇒ Literal: 0
                          └─ duration
                             ⇒ Literal: 0.1
```


### Bloqade Emulator

Anyone familiar with QuEra’s Julia SDK [**Bloqade.jl**](https://github.com/QuEraComputing/Bloqade.jl) knows that we’re pretty obsessed with performance. We would also be remiss to advertise Bloqade’s pure python emulator. While not as fast as **Bloqade.jl**, we have have worked to optimize our the state-vector simulator to get the most out of python as possible.  The emulator supports both two and three level atom configurations, along with global and local driving and support for the blockade subspace (for those who are more familiar with Rydberg atoms). The blockade subspace and matrix calculations are nearly optimal for both memory and time and are written in pure NumPy and SciPy. We also have basic Numba JIT compiled sparse operations that further optimize the memory when solving the time-dependent Schrödinger equation. We hope our python emulator will allow you to explore a wide variety of applications for neutral atoms and prototype some neat new algorithms with AHS.

> Capitalize Bloqade across the entire article [name=jzlong]

### Target Multiple Backends

All Bloqade programs can be targeted to multiple emulation and hardware backends very easily, again using the chaining of `.`’s. Also note that the chaining syntax allows Bloqade to let you know exactly when a program should be able to be run. To select `braket` as your service simply select the `braket` attribute of your program. At this stage there will be two methods availible for you, `aquila` and `local_emulator`.

> I personally prefer to distinguish between methods and attributes by putting the `()` after a method name and omitting them for attributes [name=jzlong]

Each backend has different restrictions in terms of the types of AHS programs that can be run. During the alpha phase of Bloqade we will continue to improve the error messages that are given when targeting specific backends making it easy for you to diagnose any issues with your program execution.

Depending on the backend there are two or three methods for executing your program. For Cloud devices Bloqade has an API for both asynchronous (`run_async`) and synchronous (`run`) method for executing the job. Local emulator backends only support the `run` API.

Now let us revisit the meaning of `args` assignment. Every execution method has a `args` argument, this is where you can specify the values of the parameters defined in `args`  when defining your program. The order of the arguments in the `args` tuple is the order of the variables specified in the `args` method.

> a vs an? [name=jzlong]

Finally the backend object that gets created is also callable where the such that `object(*args, shots=shots,...)` is equivalent to `object.run(shots, args=args, ...)`. While this is primarily a stylistic choice but this is an available interface for you if need be.

> "where the such that" -> "such that"
> "While this is primarily a stylistic choice but this is an available" -> "While this is primarily a stylicstic choice, this is also an available interface for you if need be" [name=jzlong]

### Job management Features

If you use the `batch_assign` API combined with your parameterized program it is possible to submit entire batches of AWS tasks. It's not enough to make programming AHS easy though; you also need to manage all the data that gets generated. Fear not, we have you covered. We know it can be quite cumbersome to have to manage hundreds or thousands of tasks so we have provided some useful functionality inside Bloqade to make your life easier as well as making experiments more reproducible.

> Fear not, we have you covered! (worth adding an exclamation mark just to go the full nine yards with the chippy/enthusiastic tone). [name=jzlong]

One of the most common issues when running AHS (or just QC in general) is saving experimental results. When using a cloud device one also has the added difficultly of associating a task id with the parameter in the parameter scan as well as checking and fetching the task results as the tasks are completed. Bloqade provides a uniform format of saving this data which is useful for users to do sharable and reproducable work. To save your results simply invoke the `save` and `load` functions. We also provide `dumps` and `loads` if you want to work directly with strings instead of JSON files! It's as simple as:

> capitalize ID [name=jzlong]

```python
from bloqade import save, load

# define program
...

batch_task = my_program.braket.aquila().run_async(100)

save(batch_task, “my_aquila_results.json”)

# in some other file:

loaded_batch_task = load(“my_aquila_results.json”)

# continue with analysis
...

```

These objects will contain all the necessary information to fetch results and obtain the values of parameters used in your program.

Saving files isn’t all that Bloqade offers. When dealing with a Cloud device like Aquila it is important to be able to manage those asynchronous tasks. Bloqade offers different ways to do this:

> "...isn't all that Bloqade offers." -> "..isn't all that Bloqade offers to make your life easier."

- `batch_task.fetch()` queries the current task statuses and fetches the results of completed tasks without blocking the python interpreter. The results are stored inside the current object.

- `batch_task.pull()` Like fetch but waits until all tasks have been completed before unblocking the interpreter. The tasks the results are stored inside the current object.

- `batch_task.get_tasks(*status_codes)` returns a new Batch object that contains the tasks with the status given by the inputs to the function

- `batch_task.remove_tasks(*status_codes)` return a new Batch object that contains tasks that did not match the status code that have been given.

See the [documentation](https://bloqade.quera.com/latest/reference/bloqade/task/batch/#bloqade.task.batch.RemoteBatch) for more details on what the various status codes are and what they mean.


## Adaptive workloads

As mentioned above, the ability to parameterize and assign values to your analog program means that there is a lot one can do in terms of running various kinds of experiments. Here we will discuss how to combine the parameterized pulses with braket’s hybrid jobs!


In this case we can pass our parameterized pulse program into classical optimizer in order to provide classical feedback for the next quantum program to run. The use case we will cover here is a pretty standard problem that maps very neatly onto the AHS architecture implemented with Neutral atoms. Because of the Rydberg blockade effect the ground state of a collection of atoms maps exactly to what is called the Maximum Independent Set (MIS) problem on geometric graphs. The MIS problem is a graph coloring problem where the goal is to find the largest set of nodes in a graph such that no two nodes are connected by an edge. This problem is NP-hard and has many applications in scheduling, resource allocation, and even quantum error correction.


> I also think it better to use the term "Combinatorial Optimization" over "Graph Coloring" considering CO might open a broader window in people's minds for what the machine is capable of than just "Graph Coloring".
> It would also be nice to have links to examples for each application (MIS for scheduling, resource allocation, QEC.)

We refer the reader to [this](https://github.com/QuEraComputing/QuEra-braket-examples/blob/main/OptimizationTutorial/AWS_optimization_demo.ipynb) Notebook example for a more detailed explanation of the problem and how it maps onto AHS. For this blog post we will focus on the implementation of the hybrid algorithm using Bloqade and Braket Hybrid Jobs.

Like most of the Bloqade programs we begin by importing the necessary components to build the program:

```python
import numpy as np
from bloqade import RB_C6, save, start, var
from bloqade.atom_arrangement import Square
from braket.devices import Devices
from braket.aws import AwsDevice
```

using the `AwsDevice` we can get some information about the capabilities of the device. Note that Bloqade uses `rad/us` and `us` for energy and time units respectively while braket uses SI unites, e.g. `rad/s` and `s`, hence the conversion of units below.

```python
# define the parameters of the experiment
device = AwsDevice(Devices.QuEra.Aquila)
rydberg_properties = device.properties.paradigm.rydberg.rydbergGlobal

# Convert energy units to rad/us and time to us
detuning_max = float(rydberg_properties.detuningRange[1]) / 1e6
rabi_max = float(rydberg_properties.rabiFrequencyRange[1]) / 1e6
total_time = float(rydberg_properties.timeMax) * 1e6
```

For the particular problem we are studying we need to map the problem graph onto the atom arrangement. For more information we refer the reader to the notebook [example](https://github.com/QuEraComputing/QuEra-braket-examples/blob/main/OptimizationTutorial/AWS_optimization_demo.ipynb).

```python
# make sure next nearest neighbors are blockaded
Rmin = np.sqrt(2) # minimum unit disk radius
Rmax = 2  # maximum unit disk radius
Rudg = np.sqrt(Rmin * Rmax) # geometric mean of Rmin and Rmax

detuning_end = detuning_max / 4 # detuning at the end of the pulse
blockade_radius = (RB_C6 / detuning_end) ** (1 / 6)
lattice_spacing = blockade_radius / Rudg
```

Now we can define the program. We will use the `var` function to define the parameters for the program. Also the cost function will involve calculating the final energy of tha atoms which can be obtained from the geometry of the program via the `rydberg_interaction` method.

```python
# define the time step for the detuning waveform
dt = 0.4
n_steps = int(total_time / dt)
# create variables for the detuning time steps
detuning_vars = [var(f"d{i}") for i in range(n_steps - 1)]

# define the lattice size before defect insertion
L = 4
# set seed for defect generation
rng = np.random.default_rng(1337)
# define the geometry of the program
geometry = (
    Square(L, lattice_spacing)
    .apply_defect_count(L**2 // 2, rng=rng)
    .remove_vacant_sites()
)
# define the program
program = (
    geometry.rydberg.detuning.uniform.piecewise_linear(
        n_steps * [dt], [-detuning_end] + detuning_vars + [detuning_end]
    )
    .amplitude.uniform.piecewise_linear(
        [0.1, total_time - 0.2, 0.1], [0, rabi_max, rabi_max, 0]
    )
)
# get the interaction matrix
V_ij = geometry.interaction_matrix()
```

We need to build the infrastructure to do the hybrid job. There are many different tools availible in `braket.jobs` that allow you to log the progress of your hybrid algorithm. Here we set up a simple class that wraps the cost function and log the progress of the algorithm.

```python
from braket.jobs import (
    InstanceConfig,
    hybrid_job,
    save_job_checkpoint,
)
from braket.jobs.metrics import log_metric
from braket.jobs_data import PersistedJobDataFormat
from braket.tracking import Tracker

# define a wrapper for the cost function for reporting
class CostFuncWrapper:
    def __init__(self, backend, shots=10, **options):
        self.backend = backend
        self.options = options
        self.iterations = 0
        self.shots = shots
        self.prev_calls = {}
        self.task_tracker = Tracker().start()

    @staticmethod
    def cost_func(report):
        bitstrings = 1 - np.asarray(report.bitstrings(False))
        detuning_energies = -detuning_end * bitstrings.sum(axis=-1)
        interaction_energies = np.einsum(
            "ij, ...i, ...j-> ...", V_ij, bitstrings, bitstrings
        )

        total_energy = detuning_energies + interaction_energies
        # minimize the energy mean and standard deviation
        return total_energy.mean() + total_energy.std()

    def __call__(self, x):
        args = tuple(x)

        batch_task = self.backend.run(self.shots, args=args, **self.options)
        report = batch_task.report()

        save(batch_task, f"my-aquila_results-{self.iterations}.json")

        self.prev_calls[args] = report
        return self.cost_func(report)

    def callback(self, state):
        args = tuple(state.x)
        self.iterations += 1
        bitstrings = 1 - np.asarray(self.prev_calls[args].bitstrings(False))
        detuning_energies = -detuning_end * bitstrings.sum(axis=-1)

        interaction_energies = np.einsum(
            "ij, ...i, ...j-> ...", V_ij, bitstrings, bitstrings
        )

        total_energy = detuning_energies + interaction_energies
        mean_energy = total_energy.mean()
        std_energy = total_energy.std()

        # Log metrics to display in Braket Console
        log_metric(
            iteration_number=self.iterations, value=state.fun, metric_name="loss"
        )
        log_metric(
            iteration_number=self.iterations,
            value=mean_energy,
            metric_name="mean energy",
        )
        log_metric(
            iteration_number=self.iterations,
            value=std_energy,
            metric_name="std energy",
        )

        # Also track the quantum task cost for Braket devices
        braket_task_cost = float(
            self.task_tracker.qpu_tasks_cost()
            + self.task_tracker.simulator_tasks_cost()
        )
        log_metric(
            metric_name="braket_cost",
            value=braket_task_cost,
            iteration_number=self.iterations,
        )

        # Save a checkpoint to resume the hybrid job from where you left off
        checkpoint_data = {"i": self.iterations, "args": args}
        save_job_checkpoint(
            checkpoint_data, data_format=PersistedJobDataFormat.PICKLED_V4
        )
        # end the job if the std energy is less than 5% of the mean energy
        # this indicates that the system is close to the ground state
        return abs(std_energy / mean_energy) < 0.05
```

While this is a lot to take in let us go through some important things. Firstly, you can generate a `Report` object from a Bloqade batch of tasks. This object provides some basic analysis methods common to Neutral atom AHS computing. The one we make the most use of here is the `bitstrings` method which return a list of arrays that contains the shot results after executing the program. It takes a boolean argument that specifies whether or not to return the bitstrings of shots where there were atoms that did not get put into a trap before the computation was executed. By default this filter is applied, but for this problem we want to include those shots in our analysis hence the `False` argument.

> No need to capitalize "Batch" unless you want to refer to the object type
> You can just say AHS, AHS Computing seems redundant
> Do we assume users know what a trap is? Might be worth having a sentence or two, just say something like "It takes a boolean argument that specifies whether or not to return the bitstrings of shots where there were atoms that did not successfully get put into position..."

Another thing to note is that our cost function not only contains the `mean` energy but also the standard deviation. The reason for this is because we are targeting an eigenstate of the final Hamiltonian which has no energy variance. This is a good way to check if the system is in the ground state. We use the ratio of the standard deviation to the mean energy as a stopping condition for the algorithm.

Finally, we have a callback function that is called after each iteration of the optimizer. This is where we can log the progress of the algorithm. We use the `Tracker` object to track the cost of the quantum tasks that are being executed. We also use the `log_metric` function to log the mean and standard deviation of the energy as well as the cost function of the quantum tasks.

Now we can define the function that will run the hybrid job.


```python
def run_algo(assigned_program, device_arn=None, n_calls=10, shots=10):
    @hybrid_job(
        device=device_arn,  # Which device to get priority access to
        dependencies="requirements.txt",  # install bloqade
        instance_config=InstanceConfig("ml.m5.large"),
    )
    def _runner(backend, shots, n_calls, **options):
        from skopt import gp_minimize

        # Braket task cost
        wrapped_cost_func = CostFuncWrapper(backend, shots=shots, **options)

        n_params = len(backend.params.args_list)
        bounds = n_params * [(-detuning_max, detuning_max)]

        result = gp_minimize(
            wrapped_cost_func,
            bounds,
            callback=wrapped_cost_func.callback,
            n_calls=n_calls,
        )

        detuning_values = {var.name: val for var, val in zip(detuning_vars, result.x)}

        return detuning_values

    if device_arn == Devices.QuEra.Aquila:  # use Aquila
        backend = assigned_program.braket.aquila()
        options = dict()
    else:  # use  bloqade emulator
        backend = assigned_program.bloqade.python()
        options = dict(atol=1e-8, rtol=1e-4, solver_name="dopri5")

    # Run the hybrid job
    return _runner(backend, n_calls, shots, **options)
```

We use the `hybrid_job` decorator to define the hybrid job. This decorator takes a `device_arn` argument which is the Amazon Resource Name (ARN) of the device you want to run the hybrid job on. There are some other options associated with the EC2 instance that is used to run the hybrid job. We will use the `InstanceConfig` object to specify the instance type and number of instances to use. `dependencies` points to a text file that contains the python dependencies needed to run this hybrid job. In this case we need `bloqade` and `scikit-optimize` in this text file.

The function `_runner` that is being decorated must take the `backend` as the first argument. This object is generated by the Bloqade API and must match the device arn that is specified in the decorator. `n_calls` is the total number of iterations of the optimizer and `shots` is the number of shots to use for each iteration. `options` is a dictionary of options that are passed to the `run` method of the backend. The return value of the function is the final value of the parameters that were optimized. We wrap the `_runner` inside `run_algo` that takes the `program` and the `device_arn` as arguments to make sure that the device requested by `hybrid_jobs` matches the device called by `bloqade` as well as setting up specialized `options` for the different `bloqade` backends.

To run the hybrid job we simply call the `run_algo` function with the assigned program and the device arn.

```python
optimal_parameters = run_algo(program.args(detuning_vars), device_arn=Devices.QuEra.Aquila)
```

Finally we can plot the results of the hybrid job.

```python
assigned_program = program.assign(**optimal_params)
assigned_program.show()
```

To run the algorithm with Bloqade emulator we simply change the device arn to None.

Full source code:

```python=
import numpy as np
from bloqade import RB_C6, save, start, var
from bloqade.atom_arrangement import Square
from braket.devices import Devices
from braket.aws import AwsDevice


# define the parameters of the experiment
device = AwsDevice(Devices.QuEra.Aquila)
rydberg_properties = device.properties.paradigm.rydberg.rydbergGlobal

# Convert energy units to rad/us and time to us
detuning_max = float(rydberg_properties.detuningRange[1]) / 1e6
rabi_max = float(rydberg_properties.rabiFrequencyRange[1]) / 1e6
total_time = float(rydberg_properties.timeMax) * 1e6


# make sure next nearest neighbors are blockaded
# unit disk minimum and maximum radii
Rmin = np.sqrt(2)  # minimum unit disk radius
Rmax = 2  # maximum unit disk radius
# choose geometric mean of Rmin and Rmax
Rudg = np.sqrt(Rmin * Rmax)

detuning_end = detuning_max / 4
blockade_radius = (RB_C6 / detuning_end) ** (1 / 6)
lattice_spacing = blockade_radius / Rudg

# define the time step for the detuning waveform
dt = 0.4
n_steps = int(total_time / dt)
# create variables for the detuning time steps
detuning_vars = [var(f"d{i}") for i in range(n_steps - 1)]

# define the lattice size before defect insertion
L = 4
# set seed for geometry generation
rng = np.random.default_rng(1337)
program = (
    Square(L, lattice_spacing)
    .apply_defect_count(L**2 // 2, rng=rng)
    .remove_vacant_sites()
    .rydberg.detuning.uniform.piecewise_linear(
        n_steps * [dt], [-detuning_end] + detuning_vars + [detuning_end]
    )
    .amplitude.uniform.piecewise_linear(
        [0.1, total_time - 0.2, 0.1], [0, rabi_max, rabi_max, 0]
    )
)
# get atom register and interaction matrix
V_ij = program.parse_register().rydberg_interaction()


from braket.jobs import (
    InstanceConfig,
    hybrid_job,
    save_job_checkpoint,
)
from braket.jobs.metrics import log_metric
from braket.jobs_data import PersistedJobDataFormat
from braket.tracking import Tracker


# define a wrapper for the cost function for reporting
class CostFuncWrapper:
    def __init__(self, cost_func, backend, shots=10, **options):
        self.backend = backend
        self.options = options
        self.iterations = 0
        self.shots = shots
        self.prev_calls = {}
        self.task_tracker = Tracker().start()

    @staticmethod
    def cost_func(report):
        bitstrings = 1 - np.asarray(report.bitstrings(False))
        detuning_energies = -detuning_end * bitstrings.sum(axis=-1)
        interaction_energies = np.einsum(
            "ij, ...i, ...j-> ...", V_ij, bitstrings, bitstrings
        )

        total_energy = detuning_energies + interaction_energies
        # minimize the energy mean and standard deviation
        return total_energy.mean() + total_energy.std()

    def __call__(self, x):
        args = tuple(x)

        batch_task = self.backend.run(self.shots, args=args, **self.options)
        report = batch_task.report()

        save(batch_task, f"my-aquila_results-{self.iterations}.json")

        self.prev_calls[args] = report
        return self.cost_func(report)

    def callback(self, state):
        args = tuple(state.x)
        self.iterations += 1
        bitstrings = 1 - np.asarray(self.prev_calls[args].bitstrings(False))
        detuning_energies = -detuning_end * bitstrings.sum(axis=-1)

        interaction_energies = np.einsum(
            "ij, ...i, ...j-> ...", V_ij, bitstrings, bitstrings
        )

        total_energy = detuning_energies + interaction_energies
        mean_energy = total_energy.mean()
        std_energy = total_energy.std()

        # Log metrics to display in Braket Console
        log_metric(
            iteration_number=self.iterations, value=state.fun, metric_name="loss"
        )
        log_metric(
            iteration_number=self.iterations,
            value=mean_energy,
            metric_name="mean energy",
        )
        log_metric(
            iteration_number=self.iterations,
            value=std_energy,
            metric_name="std energy",
        )

        # Also track the quantum task cost for Braket devices
        braket_task_cost = float(
            self.task_tracker.qpu_tasks_cost()
            + self.task_tracker.simulator_tasks_cost()
        )
        log_metric(
            metric_name="braket_cost",
            value=braket_task_cost,
            iteration_number=self.iterations,
        )

        # Save a checkpoint to resume the hybrid job from where you left off
        checkpoint_data = {"i": self.iterations, "args": args}
        save_job_checkpoint(
            checkpoint_data, data_format=PersistedJobDataFormat.PICKLED_V4
        )
        # end the job if the std energy is less than 5% of the mean energy
        # this indicates that the system is close to the ground state
        return abs(std_energy / mean_energy) < 0.05


def run_algo(assigned_program, device_arn=None, n_calls=10, shots=10):
    @hybrid_job(
        device=device_arn,  # Which device to get priority access to
        dependencies="requirements.txt",  # install bloqade
        instance_config=InstanceConfig("ml.m5.large"),
    )
    def _runner(backend, shots, n_calls, **options):
        from skopt import gp_minimize

        # Braket task cost
        wrapped_cost_func = CostFuncWrapper(backend, shots=shots, **options)

        n_params = len(backend.params.args_list)
        bounds = n_params * [(-detuning_max, detuning_max)]

        result = gp_minimize(
            wrapped_cost_func,
            bounds,
            callback=wrapped_cost_func.callback,
            n_calls=n_calls,
        )

        detuning_values = {var.name: val for var, val in zip(detuning_vars, result.x)}

        return detuning_values

    if device_arn == Devices.QuEra.Aquila:  # use Aquila
        backend = assigned_program.braket.aquila()
        options = dict()
    else:  # use  bloqade emulator
        backend = assigned_program.bloqade.python()
        options = dict(atol=1e-8, rtol=1e-4, solver_name="dopri5")

    # Run the hybrid job
    return _runner(backend, n_calls, shots, **options)


# optimal_params = run_algo(program.args(detuning_vars), Devices.QuEra.Aquila)
optimal_params = run_algo(program.args(detuning_vars), None, n_calls=10, shots=10)

assigned_program = program.assign(**optimal_params)
assigned_program.show()

```
