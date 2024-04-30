from typing import Any, Optional
import numpy as np
from pydantic.v1.dataclasses import dataclass
from pydantic.v1 import ValidationError, validator
from .tree_print import Printer
import re
from decimal import Decimal
import numbers

__all__ = [
    "var",
    "cast",
    "Scalar",
    "Interval",
    "Variable",
    "Literal",
]


@dataclass(frozen=True)
class Scalar:
    """Bloqade type used to represent and manipulate variables inside programs as well as create complex variable expressions.

    ??? abstract "Background and Context"

        # Variables and Expressions

        The Scalar type allows you to create variables which in turn can be used to create complex expressions.

        ```python
        from bloqade import cast
        # create a variable with a name
        var = cast("var")
        # create arithmetic expression using the variable
        scalar_expr = (var + 2) - 1 * 10 / 2
        # build more on the expression
        even_more_complex_expr = scalar_expr + 1
        ```

        These standalone variables or expressions created with them can be plugged in almost anywhere in a
        Bloqade program where a value is expected (see "Potential Pitfalls" below for where the scalar type cannot be used).

        ```python
        from bloqade import start
        simple_program = start.rydberg.rabi.amplitude.uniform
        apply_waveform = simple_program.constant(duration=1.0, value=scalar_expr)
        ```

        You can then assign values to variables by themselves or in expressions later in program construction using:
        [`assign`][bloqade.builder.pragmas.Assignable.assign] and [`batch_assign`][bloqade.builder.pragmas.Assignable.assign] or
        delay assignment until runtime via [`args`][bloqade.builder.pragmas.AddArgs.args] and `run` on either a
        [`BloqadePythonRoutine`][bloqade.ir.routine.bloqade.BloqadePythonRoutine] or [`BraketLocalEmulatorRoutine`][bloqade.ir.routine.braket.BraketLocalEmulatorRoutine]

        ```python
        # Remember that "var" is the name we gave the variable in our previous expression
        vars_single_assigned_program = apply_waveform.assign(var = 1.0)

        # with batch assign you can assign multiple values to the variable to create multiple versions of the program
        # which are then translated to individual quantum tasks.
        vars_batch_assigned_program = apply_waveform.batch_assign(var = [1.0, 2.0, 3.0])

        # using `args` you can delay assignment until runtime
        runtime_assignment_program = apply_waveform.args([var]).bloqade.python().run(10, args=(1.0,))
        ```

        Bloqade is also smart enough to automatically create scalar types where strings are present in a program:

        ```python
        from bloqade import start
        # Bloqade automatically turns the string in this position into a variable
        variable_position_program = start.add_position((0, "y"))

        # Strings inside waveforms can also be turned into variables
        target_rydberg_rabi_amp_program = variable_position_program.rydberg.rabi.amplitude.uniform
        variable_waveform_program = target_rydberg_rabi_amp_program.piecewise_linear(durations=[0.6, 0.4, 0.6], values=["ramp", "hold", "ramp"])
        ```

        # Scalar Literals

        Scalar literals are a special type of scalar that can be used to avoid floating point rounding errors in your program. Instead of
        directly plugging in floating point numbers into your Bloqade program you may first convert them to scalar Literals and then use them in your program.

        ```python
        from bloqade import start, cast
        geometry = start.add_position((0,0))
        target_rydberg_rabi_amplitude = geometry.rydberg.rabi.amplitude.uniform

        waveform_times = cast([0.4, 1.0, 0.4])
        waveform_values = cast([0.0, 3.0, 3.0, 0.0])

        waveform_applied = target_rydberg_rabi_amplitude.piecewise_linear(durations=waveform_times, values=waveform_values)
        ```

        # Scalar Grammar

        For more advanced users you can find the grammar for scalar expressions below:
        ```bnf
        <scalar> ::= <literal>
        | <variable>
        | <default>
        | <negative>
        | <add>
        | <mul>
        | <min>
        | <max>
        | <slice>
        | <interval>

        <mul> ::= <scalar> '*' <scalar>
        <add> ::= <scalar> '+' <scalar>
        <min> ::= 'min' <scalar>+
        <max> ::= 'max' <scalar>+
        <slice> ::= <scalar expr> '[' <interval> ']'
        <interval> ::= <scalar expr> '..' <scalar expr>
        <real> ::= <literal> | <var>
        ```

    ??? example "Examples"

        Assign a single value to a variable in a program:

        ```python
        from bloqade import start
        geometry = start.add_position((0,0))
        target_rydberg_rabi_amplitude = geometry.rydberg.rabi.amplitude.uniform
        waveform_applied = target_rydberg_rabi_amplitude.constant(duration=1.0, value="waveform_value")
        variables_assigned = waveform_applied.assign(waveform_value=1.0)
        ```

        Sweep over a range of values for an atom position in a program

        ```python
        from bloqade import start
        # Use a string in position coordinate, Bloqade automatically converts it to a variable
        variable_geometry = start.add_position([(0, 0), (0, "atom_distance")])
        target_rydberg_rabi_amplitude = variable_geometry.rydberg.rabi.amplitude.uniform
        waveform_applied = target_rydberg_rabi_amplitude.constant(duration=1.0, value=1.0)

        # assign multiple values to multiple variables
        variable_assigned_program = waveform_applied.batch_assign(atom_distance=[1.0, 2.0, 3.0])
        ```

        Sweep over a range of values for a waveform amplitude in a program:

        ```python
        from bloqade import start
        geometry = start.add_position((0,0))
        target_rydberg_rabi_amplitude = geometry.rydberg.rabi.amplitude.uniform
        waveform_applied = target_rydberg_rabi_amplitude.piecewise_linear(duration=[0.4, 1.0, 0.4], value=[0, "hold", "hold", 0])

        variable_assigned_program = waveform_applied.batch_assign(hold=[0.0, 1.0, 2.0])
        ```

        Sweep over multiple variables in parallel in a program
        ```python
        from bloqade import start
        geometry = start.add_position([(0,0), (0, "atom_distance")])
        target_rydberg_rabi_amplitude = geometry.rydberg.rabi.amplitude.uniform
        waveform_applied = target_rydberg_rabi_amplitude.constant(duration=1.0, value="waveform_value")

        variable_assigned_program = waveform_applied.batch_assign(waveform_value=[1.0, 2.0, 3.0], atom_distance=[1.0, 2.0, 3.0])
        ```

    ??? info "Applications"
        * [Single Qubit Rabi Oscillations](https://queracomputing.github.io/bloqade-python-examples/latest/examples/example-1-rabi/)
        * [Single Qubit Ramsey Protocol](https://queracomputing.github.io/bloqade-python-examples/latest/examples/example-1-ramsey/)
        * [Single Qubit Floquet Dynamics](https://queracomputing.github.io/bloqade-python-examples/latest/examples/example-1-floquet/)
        * [Two Qubit Adiabatic Sweep](https://queracomputing.github.io/bloqade-python-examples/latest/examples/example-2-two-qubit-adiabatic/)
        * [Multi-qubit Blockaded Rabi Oscillations](https://queracomputing.github.io/bloqade-python-examples/latest/examples/example-2-multi-qubit-blockaded/)
        * [Nonequilibrium Dynamics of nearly Blockaded Rydberg Atoms](https://queracomputing.github.io/bloqade-python-examples/latest/examples/example-2-nonequilibrium-dynamics-blockade-radius/)
        * [1D Z2 State Preparation](https://queracomputing.github.io/bloqade-python-examples/latest/examples/example-3-time-sweep/)
        * [2D State Preparation](https://queracomputing.github.io/bloqade-python-examples/latest/examples/example-3-2d-ordered-state/)
        * [Quantum Scar Dynamics](https://queracomputing.github.io/bloqade-python-examples/latest/examples/example-4-quantum-scar-dynamics/)
        * [Solving the Maximal Independent Set Problem on defective King Graph](https://queracomputing.github.io/bloqade-python-examples/latest/examples/example-5-MIS-UDG/)
        * [Lattice Gauge Theory Simulation](https://queracomputing.github.io/bloqade-python-examples/latest/examples/example-6-lattice-gauge-theory/)

    ??? warning "Potential Pitfalls"

        # No Scalars After Assignment

        Scalars cannot be plugged in to your program after you have called [`assign`][bloqade.builder.pragmas.Assignable.assign] or [`batch_assign`][bloqade.builder.pragmas.BatchAssignable.batch_assign] on a program.

        # Parallelize Does Not Take Scalars

        The [`parallelize`][bloqade.builder.pragmas.Parallelizable.parallelize] method will only take a [`LiteralType`][bloqade.builder.typing.LiteralType] and not a Scalar type.

        # No Automatic Cartesian Product

        If you have a program that has multiple variables like the one below:
        ```python
        from bloqade import start
        geometry = start.add_position([(0,0), (0, "atom_distance")])
        target_rydberg_rabi_amplitude = geometry.rydberg.rabi.amplitude.uniform
        waveform_applied = target_rydberg_rabi_amplitude.constant(duration=1.0, value="waveform_value")

        variables_assigned = waveform_applied.batch_assign(waveform_value=[1.0, 2.0, 3.0], atom_distance=[1.0, 2.0, 3.0])
        ```

        The resulting tasks generated will NOT follow the assignment pattern:
        ```
        Task 1:
        - waveform_value = 1.0, atom_distance = 1.0
        Task 2:
        - waveform_value = 1.0, atom_distance = 2.0
        Task 3:
        - waveform_value = 1.0, atom_distance = 3.0
        Task 4:
        - waveform_value = 2.0, atom_distance = 1.0
        ...
        ```

        Instead, the tasks generated will consume the list of assigned values in parallel:
        ```
        Task 1:
        - waveform_value = 1.0, atom_distance = 1.0
        Task 2:
        - waveform_value = 2.0, atom_distance = 2.0
        Task 3:
        - waveform_value = 3.0, atom_distance = 3.0
        ```

        # Assigned Values to Variables Must Be Equal in Length

        Due to the behavior mentioned above, if you assign to one variable a list of values with a certain length,
        then the other variables in the program must also be assigned lists of the same length.

    """

    def __getitem__(self, s: slice) -> "Scalar":
        return Scalar.canonicalize(Slice(self, Interval.from_slice(s)))

    def __add__(self, other: "Scalar") -> "Scalar":
        return self.add(other)

    def __sub__(self, other: "Scalar") -> "Scalar":
        return self.sub(other)

    def __mul__(self, other: "Scalar") -> "Scalar":
        return self.mul(other)

    def __truediv__(self, other: "Scalar") -> "Scalar":
        return self.div(other)

    def __radd__(self, other: "Scalar") -> "Scalar":
        try:
            lhs = cast(other)
        except TypeError:
            return NotImplemented

        if not isinstance(lhs, Scalar):
            return NotImplemented

        return lhs.add(self)

    def __rsub__(self, other: "Scalar") -> "Scalar":
        try:
            lhs = cast(other)
        except TypeError:
            return NotImplemented

        if not isinstance(lhs, Scalar):
            return NotImplemented

        return lhs.sub(self)

    def __rmul__(self, other: "Scalar") -> "Scalar":
        try:
            lhs = cast(other)
        except TypeError:
            return NotImplemented

        if not isinstance(lhs, Scalar):
            return NotImplemented

        return lhs.mul(self)

    def __rtruediv__(self, other: "Scalar") -> "Scalar":
        try:
            lhs = cast(other)
        except TypeError:
            return NotImplemented

        if not isinstance(lhs, Scalar):
            return NotImplemented

        return lhs.div(self)

    def __neg__(self) -> "Scalar":
        return Scalar.canonicalize(Negative(self))

    def add(self, other) -> "Scalar":
        try:
            rhs = cast(other)
        except TypeError:
            return NotImplemented

        if not isinstance(rhs, Scalar):
            return NotImplemented

        expr = Add(lhs=self, rhs=rhs)
        return Scalar.canonicalize(expr)

    def sub(self, other) -> "Scalar":
        try:
            rhs = cast(other)
        except TypeError:
            return NotImplemented

        if not isinstance(rhs, Scalar):
            return NotImplemented

        expr = Add(lhs=self, rhs=-rhs)
        return Scalar.canonicalize(expr)

    def mul(self, other) -> "Scalar":
        try:
            rhs = cast(other)
        except TypeError:
            return NotImplemented

        if not isinstance(rhs, Scalar):
            return NotImplemented

        expr = Mul(lhs=self, rhs=rhs)
        return Scalar.canonicalize(expr)

    def div(self, other) -> "Scalar":
        try:
            rhs = cast(other)
        except TypeError:
            return NotImplemented

        if not isinstance(rhs, Scalar):
            return NotImplemented

        expr = Div(lhs=self, rhs=rhs)
        return Scalar.canonicalize(expr)

    def min(self, other) -> "Scalar":
        try:
            other_expr = cast(other)
        except TypeError:
            return NotImplemented

        expr = Min(exprs=frozenset({self, other_expr}))
        return Scalar.canonicalize(expr)

    def max(self, other) -> "Scalar":
        try:
            other_expr = cast(other)
        except TypeError:
            return NotImplemented

        expr = Max(exprs=frozenset({self, other_expr}))
        return Scalar.canonicalize(expr)

    def __str__(self) -> str:
        ph = Printer()
        ph.print(self)
        return ph.get_value()

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)

    @staticmethod
    def canonicalize(expr: "Scalar") -> "Scalar":
        from bloqade.compiler.rewrite.common.canonicalize import Canonicalizer

        return Canonicalizer().visit(expr)


def check_variable_name(name: str) -> None:
    regex = "^[A-Za-z_][A-Za-z0-9_]*"
    re_match = re.match(regex, name)
    if re_match.group() != name:
        raise ValidationError(f"string '{name}' is not a valid python identifier")


def cast(py) -> "Scalar":
    """
    Converts certain python objects to [`Scalar`][bloqade.ir.scalar.Scalar] types.

    Args:
        py (Union[str,Real,Tuple[Real],List[Real]]): python object to cast

    Returns:
        Scalar: A Scalar variable or a Scalar literal, usable in more complex expressions.


    ??? abstract "Background and Context"

        Bloqade has its own [`Scalar`][bloqade.ir.scalar.Scalar] type which is used to represent and manipulate variables inside programs as well as create complex expressions.

        `cast` allows you to create these Scalar types. Specifically, you can create:
        * Scalar variables, which can be plugged into a Bloqade program and later assigned single or multiple values
        * Scalar literals, which can also be plugged into a Bloqade program with the benefit that you can avoid floating point rounding errors.

        As an example, if you want to create a single variable you can do the following:

        ```python
        from bloqade import cast
        my_var = cast("my_var")
        ```

        You can also create a list or tuple of variables by providing a list or tuple of strings:

        ```python
        from bloqade import cast
        list_of_vars = cast(["var1", "var2", "var3"])
        tuple_of_vars = cast(["var1", "var2", "var3"])
        ```

        As well as a single Scalar Literal or multiple through the same means:

        ```python
        from bloqade import cast
        single_scalar_literal = cast(1.0)
        multiple_scalar_literals = cast([1.0, 2.0, 3.0])
        ```

    ??? example "Examples"

        In this example we take advantage of `cast` to first define a set of variables
        which we can then `sum` over (using Python's standard `sum` implementation) to
        make it easier for us to define the duration of a subsequent waveform.

        ```python
        from bloqade import cast, start

        durations = cast(["ramp_time", "run_time", "ramp_time"])

        geometry = start.add_position((0,0))
        rydberg_rabi_amplitude = geometry.rydberg.rabi.amplitude.uniform
        rabi_amplitude_waveform = rydberg_rabi_amplitude.piecewise_linear(durations=durations, values=[0, 3.0, 3.0, 0])
        detuning_waveform = rabi_amplitude_waveform.detuning.uniform.constant(duration=sum(durations), value=1.0)
        ```

    ??? info "Applications"
        * [Single Qubit Rabi Oscillations](https://queracomputing.github.io/bloqade-python-examples/latest/examples/example-1-rabi/)
        * [Single Qubit Ramsey Protocol](https://queracomputing.github.io/bloqade-python-examples/latest/examples/example-1-ramsey/)
        * [Single Qubit Floquet Dynamics](https://queracomputing.github.io/bloqade-python-examples/latest/examples/example-1-floquet/)
        * [Two Qubit Adiabatic Sweep](https://queracomputing.github.io/bloqade-python-examples/latest/examples/example-2-two-qubit-adiabatic/)
        * [Lattice Gauge Theory Simulation](https://queracomputing.github.io/bloqade-python-examples/latest/examples/example-6-lattice-gauge-theory/)
    """
    ret = trycast(py)
    if ret is None:
        raise TypeError(f"Cannot cast {type(py)} to Scalar Literal")

    return ret


# TODO: RL: remove support on List and Tuple just use map?
#       this is making type inference much harder to parse
#       in human brain
# [KHW] it need to be there. For recursive replace for nested
#       list/tuple
def trycast(py) -> Optional[Scalar]:
    if isinstance(py, (int, bool, numbers.Real)):
        return Literal(Decimal(str(py)))
    elif isinstance(py, Decimal):
        return Literal(py)
    elif isinstance(py, str):
        return Variable(py)
    elif isinstance(py, Scalar):
        return py
    elif isinstance(py, (list, tuple)):
        return type(py)(map(cast, py))
    elif isinstance(py, np.ndarray):
        return np.array(list(map(cast, py)))
    else:
        return


def var(py: str) -> "Variable":
    """Convert a string or a list/tuple of strings to a [`Scalar`][bloqade.ir.scalar.Scalar] variable type.

    Args:
        py (Union[str, List[str], Tuple[str]]): a string or list/tuple of strings

    Returns:
        Variable: a single Scalar variable or a list/tuple of Scalar variables.

    ??? abstract "Background and Context"

        Bloqade has its own [`Scalar`][bloqade.ir.scalar.Scalar] type which is used to represent and manipulate variables inside programs as well as create complex expressions.

        `var` allows you to create these variables which can then be plugged into a Bloqade program and later assigned single or multiple values.

        You can convert a single string to a variable:

        ```python
        from bloqade import var
        my_var = var("my_var")
        ```

        Or a list/tuple of strings into a list/tuple of variables:

        ```python
        from bloqade import var
        multiple_vars = var(["var1", "var2", "var3"])
        ```

    ??? example "Examples"

        Here we use `var` to create a set of variables and then assign values to them afterwards:

        ```python
        from bloqade import var

        durations = var(["ramp_time", "run_time", "ramp_time"])

        geometry = start.add_position((0,0))
        rydberg_rabi_amplitude = geometry.rydberg.rabi.amplitude.uniform
        rabi_amplitude_waveform = rydberg_rabi_amplitude.piecewise_linear(durations=durations, values=[0, 3.0, 3.0, 0])

        assigned_variables = rabi_amplitude_waveform.assign(ramp_time=0.2, run_time=0.4)
        ```

    ??? info "Applications"

        * [Two Qubit Adiabatic Sweep](https://queracomputing.github.io/bloqade-python-examples/latest/examples/example-2-two-qubit-adiabatic/)
        * [Quantum Scar Dynamics](https://queracomputing.github.io/bloqade-python-examples/latest/examples/example-4-quantum-scar-dynamics/)
        * [Solving the Maximal Independent Set Problem on defective King Graph](https://queracomputing.github.io/bloqade-python-examples/latest/examples/example-5-MIS-UDG/)

    """
    ret = tryvar(py)
    if ret is None:
        raise TypeError(f"Cannot cast {type(py)} to Variable")

    return ret


def tryvar(py) -> Optional["Variable"]:
    if isinstance(py, str):
        return Variable(py)
    if isinstance(py, Variable):
        return py
    elif isinstance(py, (list, tuple)):
        return type(py)(map(var, py))
    else:
        return


class Real(Scalar):
    # """Base class for all real expressions."""
    pass


@dataclass(frozen=True)
class Literal(Real):
    """Scalar Literal type. See [Scalar][bloqade.ir.scalar.Scalar] for more information."""

    value: Decimal

    def __call__(self, **assignments) -> Decimal:
        return self.value

    def __str__(self) -> str:
        return str(self.value)

    def children(self):
        return []

    def print_node(self):
        return f"Literal: {self.value}"

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


@dataclass(frozen=True)
class Variable(Real):
    """Scalar Variable type. See [Scalar][bloqade.ir.scalar.Scalar] for more information."""

    name: str

    def __call__(self, **assignments) -> Decimal:
        if self.name not in assignments:
            raise ValueError(f"Variable {self.name} not assigned")

        return Decimal(str(assignments[self.name]))

    def __str__(self) -> str:
        return self.name

    def children(self):
        return []

    def print_node(self):
        return f"Variable: {self.name}"

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)

    @validator("name", allow_reuse=True)
    def validate_name(cls, name):
        check_variable_name(name)
        if name in ["__batch_params"]:
            raise ValidationError(
                "Cannot use reserved name `__batch_params` for variable name"
            )

        return name


@dataclass(frozen=True)
class AssignedVariable(Scalar):
    name: str
    value: Decimal

    def __call__(self, **assignments) -> Decimal:
        if self.name in assignments:
            raise ValueError(f"Variable {self.name} already assigned")

        return self.value

    def __str__(self) -> str:
        return f"{self.name}"

    def children(self):
        return []

    def print_node(self):
        return f"AssignedVariable: {self.name} = {self.value!s}"

    @validator("name", allow_reuse=True)
    def validate_name(cls, name):
        check_variable_name(name)
        if name in ["__batch_params"]:
            raise ValidationError(
                "Cannot use reserved name `__batch_params` for variable name"
            )

        return name


@dataclass(frozen=True)
class Negative(Scalar):
    expr: Scalar

    def __call__(self, **assignments) -> Decimal:
        return -self.expr(**assignments)

    def __str__(self) -> str:
        return f"-({self.expr!s})"

    def children(self):
        return [self.expr]

    def print_node(self):
        return "Negative"


@dataclass(frozen=True)
class Interval:
    start: Optional[Scalar]
    stop: Optional[Scalar]

    @staticmethod
    def from_slice(s: slice) -> "Interval":
        start, stop, step = s.start, s.stop, s.step

        if start is None and stop is None and step is None:
            raise ValueError("Slice must have at least one argument")
        elif step is not None:
            raise ValueError("Slice step must be None")

        else:
            if start is None:
                start = None
            else:
                start = cast(start)
                if not isinstance(start, Scalar):
                    raise ValueError("Slice start must be Scalar")

            if stop is None:
                stop = None
            else:
                stop = cast(stop)
                if not isinstance(stop, Scalar):
                    raise ValueError("Slice stop must be Scalar")

            return Interval(start, stop)

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)

    def __str__(self):
        if self.start is None:
            if self.stop is None:
                raise ValueError("Interval must have at least one bound")
            else:
                return f":{str(self.stop)}"
        else:
            if self.stop is None:
                return f"{str(self.start)}:"
            else:
                return f"{str(self.start)}:{str(self.stop)}"

    def print_node(self):
        return "Interval"

    def children(self):
        if self.start is None:
            if self.stop is None:
                raise ValueError("Interval must have at least one bound")
            else:
                return {"stop": self.stop}
        else:
            if self.stop is None:
                return {"start": self.start}
            else:
                return {"start": self.start, "stop": self.stop}


@dataclass(frozen=True)
class Slice(Scalar):
    expr: Scalar  # duration
    interval: Interval

    def __call__(self, **assignments) -> Decimal:
        dur = self.expr(**assignments)
        start = (
            self.interval.start(**assignments)
            if self.interval.start is not None
            else Decimal("0")
        )
        stop = (
            self.interval.stop(**assignments) if self.interval.stop is not None else dur
        )

        if start < 0:
            raise ValueError(
                f"Slice start must be non-negative, got {start} from expr:\n"
                f"{repr(self.interval.start)}\n"
                f"with assignments: {assignments}"
            )

        if stop > dur:
            raise ValueError(
                "Slice stop must be smaller or equal to than duration "
                f"{dur}, got {stop} from expr:\b"
                f"{repr(self.interval.stop)}\n"
                f"with assignments: {assignments}"
            )

        ret = stop - start

        if ret < 0:
            raise ValueError(
                f"start is larger than stop, get start = {start} and stop = {stop}\n"
                "from start expr:\n"
                f"{repr(self.interval.start)}\n"
                "and stop expr:\n"
                f"{repr(self.interval.stop)}\n"
                f"with assignments: {assignments}"
            )

        return ret

    def __str__(self) -> str:
        return f"({self.expr!s})[{self.interval!s}]"

    def children(self):
        return {"Scalar": self.expr, None: self.interval}

    def print_node(self):
        return "Slice"


@dataclass(frozen=True)
class Add(Scalar):
    lhs: Scalar
    rhs: Scalar

    def __call__(self, **assignments) -> Decimal:
        return self.lhs(**assignments) + self.rhs(**assignments)

    def __str__(self) -> str:
        return f"({self.lhs!s} + {self.rhs!s})"

    def children(self):
        return [self.lhs, self.rhs]

    def print_node(self):
        return "+"


@dataclass(frozen=True)
class Mul(Scalar):
    lhs: Scalar
    rhs: Scalar

    def __call__(self, **assignments) -> Decimal:
        return self.lhs(**assignments) * self.rhs(**assignments)

    def __str__(self) -> str:
        return f"({self.lhs!s} * {self.rhs!s})"

    def children(self):
        return [self.lhs, self.rhs]

    def print_node(self):
        return "*"


@dataclass(frozen=True)
class Div(Scalar):
    lhs: Scalar
    rhs: Scalar

    def __call__(self, **assignments) -> Decimal:
        return self.lhs(**assignments) / self.rhs(**assignments)

    def __str__(self) -> str:
        return f"({self.lhs!s} / {self.rhs!s})"

    def children(self):
        return [self.lhs, self.rhs]

    def print_node(self):
        return "/"


@dataclass(frozen=True)
class Min(Scalar):
    exprs: frozenset[Scalar]

    def __call__(self, **assignments) -> Any:
        return min(expr(**assignments) for expr in self.exprs)

    def __str__(self) -> str:
        return f"min({', '.join(map(str, self.exprs))})"

    def children(self):
        return list(self.exprs)

    def print_node(self):
        return "min"


@dataclass(frozen=True)
class Max(Scalar):
    exprs: frozenset[Scalar]

    def __call__(self, **assignments) -> Any:
        return max(expr(**assignments) for expr in self.exprs)

    def children(self):
        return list(self.exprs)

    def print_node(self):
        return "max"

    def __str__(self) -> str:
        return f"max({', '.join(map(str, self.exprs))})"
