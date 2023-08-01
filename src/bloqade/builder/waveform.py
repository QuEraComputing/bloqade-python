from .base import Builder
from .terminate import Terminate
import bloqade.ir as ir
from typing import Union, List, Callable, Optional

ScalarType = Union[float, str]


class Waveform(Builder):
    def linear(self, start: ScalarType, stop: ScalarType, duration: ScalarType):
        """
        Append/assign a linear waveform to the current location.

        Args:
            start (ScalarType Union[float, str]): The start value of the waveform
            stop (ScalarType Union[float, str]): The stop value of the waveform
            duration (ScalarType Union[float, str]): The duration of the waveform

        Examples:
            - specify a linear waveform for (spatial) uniform rydberg detuning
            from 0 to 1 in 0.5 us.

            >>> node = bloqade.start.rydberg.detuning.uniform
            >>> node = node.linear(start=0,stop=1,duration=0.5)

        Possible Next:

        - Possible Next <Location>:

            -> `.location(int)`
                :: continue building the waveform sequence,
                Addressing another location

        - Possible Next <WaveForm:: current>:

            -> `.slice()`
                :: slice current waveform

            -> `.record(str)`
                :: record the value of waveform at current time

        - Possible Next <WaveForm:: append>:

            -> `.linear()`

            -> `.constant()`

            -> `.ploy()`

            -> `.apply()`

            -> `.piecewise_linear()`

            -> `.piecewise_constant()`

            -> `.fn()`

        - Possible Next <LevelCoupling>:

            -> `.rydberg`
                :: Switch to specify rydberg level coupling channel

            -> `.hyperfine`
                :: Switch to specify hyperfine level coupling channel

        - Possible Next <Emit:: Linking Vars>:

            -> `.assign()`
                :: assign varialbe an actual value/number

            -> `.batch_assign()`
                :: create batch job with different
                sets of values assign to each variable.

        - Possible Next <Emit:: Compile >:

            -> `.quera()`
                :: Compile current program to QuEra job

            -> `.braket()`
                :: Compile current program to Amazon Braket job

            -> `.braket_local_simulator()`
                :: Compile current program to local simulator job

        """
        return Linear(self, start, stop, duration)

    def constant(self, value: ScalarType, duration: ScalarType):
        """
        Append/assign a constant waveform to the current location.

        Args:
            value (ScalarType Union[float, str]): The value of the waveform
            duration (ScalarType Union[float, str]): The duration of the waveform

        Examples:
            - specify a constant waveform of value 1 with duration 0.5
            for (spatial) uniform rydberg detuning

            >>> node = bloqade.start.rydberg.detuning.uniform
            >>> node = node.constant(value=1,duration=0.5)

        Possible Next:

        - Possible Next <Location>:

            -> `.location(int)`
                :: continue building the waveform sequence,
                Addressing another location

        - Possible Next <WaveForm:: current>:

            -> `.slice()`
                :: slice current waveform

            -> `.record(str)`
                :: record the value of waveform at current time

        - Possible Next <WaveForm:: append>:

            -> `.linear()`

            -> `.constant()`

            -> `.ploy()`

            -> `.apply()`

            -> `.piecewise_linear()`

            -> `.piecewise_constant()`

            -> `.fn()`

        - Possible Next <LevelCoupling>:

            -> `.rydberg`
                :: Switch to specify rydberg level coupling channel

            -> `.hyperfine`
                :: Switch to specify hyperfine level coupling channel

        - Possible Next <Emit:: Linking Vars>:

            -> `.assign()`
                :: assign varialbe an actual value/number

            -> `.batch_assign()`
                :: create batch job with different sets
                of values assign to each variable.

        - Possible Next <Compile>:

            -> `.quera()`
                :: Compile current program to QuEra job

            -> `.braket()`
                :: Compile current program to Amazon Braket job

            -> `.braket_local_simulator()`
                :: Compile current program to local simulator job



        """
        return Constant(self, value, duration)

    def poly(self, coeffs: ScalarType, duration: ScalarType):
        """
        Append/assign a waveform with polynomial profile to the current location.
        with form:

            wv(t) = coeffs[0] + coeffs[1]*t + coeffs[2]*t^2 + ... + coeffs[n]*t^n

        Args:
            coeffs (ScalarType Union[float, str]): The coefficients of the polynomial
            duration (ScalarType Union[float, str]): The duration of the waveform

        Examples:
            - specify a second order polynomial with duration 0.5
            for (spatial) uniform rydberg detuning

            >>> node = bloqade.start.rydberg.detuning.uniform
            >>> node = node.poly(coeffs=[1,2,3],duration=0.5)

        Possible Next:

        - Possible Next <Location>:

            -> `.location(int)`
                :: continue building the waveform sequence,
                Addressing another location

        - Possible Next <WaveForm:: current>:

            -> `.slice()`
                :: slice current waveform

            -> `.record(str)`
                :: record the value of waveform at current time

        - Possible Next <WaveForm:: append>:

            -> `.linear()`

            -> `.constant()`

            -> `.ploy()`

            -> `.apply()`

            -> `.piecewise_linear()`

            -> `.piecewise_constant()`

            -> `.fn()`

        - Possible Next <LevelCoupling>:

            -> `.rydberg`
                :: Switch to specify rydberg level coupling channel

            -> `.hyperfine`
                :: Switch to specify hyperfine level coupling channel

        - Possible Next <Emit:: Linking Vars>:

            -> `.assign()`
                :: assign varialbe an actual value/number

            -> `.batch_assign()`
                :: create batch job with different sets
                of values assign to each variable.

        - Possible Next <Compile>:

            -> `.quera()`
                :: Compile current program to QuEra job

            -> `.braket()`
                :: Compile current program to Amazon Braket job

            -> `.braket_local_simulator()`
                :: Compile current program to local simulator job



        """
        return Poly(self, coeffs, duration)

    def apply(self, wf: ir.Waveform):
        """
        Apply a pre-defined waveform to the current location.

        Args:
            wf (ir.Waveform): the waveform

        Examples:
            - apply a pre-defined waveform object to current sequence.

            >>> node = bloqade.start.rydberg.detuning.uniform
            >>> wv = bloqade.ir.Linear(0,10,0.5)
            >>> node = node.apply(wv)

        Possible Next:

        - Possible Next <Location>:

            -> `.location(int)`
                :: continue building the waveform sequence,
                Addressing another location

        - Possible Next <WaveForm:: current>:

            -> `.slice()`
                :: slice current waveform

            -> `.record(str)`
                :: record the value of waveform at current time

        - Possible Next <WaveForm:: append>:

            -> `.linear()`

            -> `.constant()`

            -> `.ploy()`

            -> `.apply()`

            -> `.piecewise_linear()`

            -> `.piecewise_constant()`

            -> `.fn()`

        - Possible Next <LevelCoupling>:

            -> `.rydberg`
                :: Switch to specify rydberg level coupling channel

            -> `.hyperfine`
                :: Switch to specify hyperfine level coupling channel

        - Possible Next <Emit:: Linking Vars>:

            -> `.assign()`
                :: assign varialbe an actual value/number

            -> `.batch_assign()`
                :: create batch job with different sets
                of values assign to each variable.

        - Possible Next <Compile>:

            -> `.quera()`
                :: Compile current program to QuEra job

            -> `.braket()`
                :: Compile current program to Amazon Braket job

            -> `.braket_local_simulator()`
                :: Compile current program to local simulator job



        """
        return Apply(self, wf)

    def piecewise_linear(self, durations: List[ScalarType], values: List[ScalarType]):
        """
        Append/assign a piecewise linear waveform to the current location.
        The durations should have number of elements = len(values) - 1.

        This function create a waveform by connecting `values[i], values[i+1]`
        with linear segments.

        Args:
            durations (List[ScalarType]): The durations of each linear segment
            values (List[ScalarType]): The values of each linear segment

        Examples:
            - specify a piecewise linear of [0,1,1,0] with duration [0.1,3.8,0.1]
            for (spatial) uniform rydberg detuning.

            >>> node = bloqade.start.rydberg.detuning.uniform
            >>> node = node.piecewise_linear(values=[0,1,1,0],durations=[0.1,3.8,0.1])

        Note:
            ScalarType can be either float or str.

        Possible Next:

        - Possible Next <Location>:

            -> `.location(int)`
                :: continue building the waveform sequence,
                Addressing another location

        - Possible Next <WaveForm:: current>:

            -> `.slice()`
                :: slice current waveform

            -> `.record(str)`
                :: record the value of waveform at current time

        - Possible Next <WaveForm:: append>:

            -> `.linear()`

            -> `.constant()`

            -> `.ploy()`

            -> `.apply()`

            -> `.piecewise_linear()`

            -> `.piecewise_constant()`

            -> `.fn()`

        - Possible Next <LevelCoupling>:

            -> `.rydberg`
                :: Switch to specify rydberg level coupling channel

            -> `.hyperfine`
                :: Switch to specify hyperfine level coupling channel

        - Possible Next <Emit:: Linking Vars>:

            -> `.assign()`
                :: assign varialbe an actual value/number

            -> `.batch_assign()`
                :: create batch job with different sets
                of values assign to each variable.

        - Possible Next <Compile>:

            -> `.quera()`
                :: Compile current program to QuEra job

            -> `.braket()`
                :: Compile current program to Amazon Braket job

            -> `.braket_local_simulator()`
                :: Compile current program to local simulator job

        """
        builder = self
        if len(durations) != len(values) - 1:
            raise ValueError("len(durations) must be len(values)-1.")

        for duration, start, stop in zip(durations, values[:-1], values[1:]):
            builder = builder.linear(start, stop, duration)

        return builder

    def piecewise_constant(self, durations: List[ScalarType], values: List[ScalarType]):
        """
        Append/assign a piecewise constant waveform to the current location.
        The durations should have number of elements = len(values).

        This function create a waveform of piecewise_constant of
        `values[i]` with duration `durations[i]`.

        Args:
            durations (List[ScalarType]): The durations of each constant segment
            values (List[ScalarType]): The values of each constant segment

        Note:
            ScalarType can be either float or str.

        Examples:
            - specify a piecewise constant of [0.5,1.5] with duration [0.1,3.8]
            for (spatial) uniform rydberg detuning.

            >>> node = bloqade.start.rydberg.detuning.uniform
            >>> node = node.piecewise_constant(values=[0.5,1.5],durations=[0.1,3.8])

        Possible Next:

        - Possible Next <Location>:

            -> `.location(int)`
                :: continue building the waveform sequence,
                Addressing another location

        - Possible Next <WaveForm:: current>:

            -> `.slice()`
                :: slice current waveform

            -> `.record(str)`
                :: record the value of waveform at current time

        - Possible Next <WaveForm:: append>:

            -> `.linear()`

            -> `.constant()`

            -> `.ploy()`

            -> `.apply()`

            -> `.piecewise_linear()`

            -> `.piecewise_constant()`

            -> `.fn()`

        - Possible Next <LevelCoupling>:

            -> `.rydberg`
                :: Switch to specify rydberg level coupling channel

            -> `.hyperfine`
                :: Switch to specify hyperfine level coupling channel

        - Possible Next <Emit:: Linking Vars>:

            -> `.assign()`
                :: assign varialbe an actual value/number

            -> `.batch_assign()`
                :: create batch job with different sets
                of values assign to each variable.


        - Possible Next <Compile>:

            -> `.quera()`
                :: Compile current program to QuEra job

            -> `.braket()`
                :: Compile current program to Amazon Braket job

            -> `.braket_local_simulator()`
                :: Compile current program to local simulator job


        """
        builder = self
        if len(durations) != len(values):
            raise ValueError("durations and values lists must have same length.")

        for duration, value in zip(durations, values):
            builder = builder.constant(value, duration)

        return builder

    def fn(self, fn: Callable, duration: ScalarType):
        """
        Append/assign a waveform defined by a python function to the current location.

        This function create a waveform with user-defined
        python function `fn(t)` with duration `duration`.

        Args:
            fn (Callable): The python function defining the waveform
            duration (ScalarType): The durations of each constant segment

        Note:
            - ScalarType can be either float or str.
            - The python function should take a single argument `t` and return a float.


        Examples:
            - create a cosine waveform with duration 0.5
            for (spatial) uniform rydberg detuning.

            >>> import numpy as np
            >>> def my_fn(t):
            >>>     return np.cos(2*np.pi*t)
            >>> node = bloqade.start.rydberg.detuning.uniform
            >>> node = node.fn(my_fn,duration=0.5)

        Possible Next:

        - Possible Next <Location>:

            -> `.location(int)`
                :: continue building the waveform sequence,
                Addressing another location

        - Possible Next <WaveForm:: current>:

            -> `.slice()`
                :: slice current waveform

            -> `.record(str)`
                :: record the value of waveform at current time

            -> `.sample()`
                :: sample the current callable at given time points.

        - Possible Next <WaveForm:: append>:

            -> `.linear()`

            -> `.constant()`

            -> `.ploy()`

            -> `.apply()`

            -> `.piecewise_linear()`

            -> `.piecewise_constant()`

            -> `.fn()`

        - Possible Next <LevelCoupling>:

            -> `.rydberg`
                :: Switch to specify rydberg level coupling channel

            -> `.hyperfine`
                :: Switch to specify hyperfine level coupling channel

        - Possible Next <Emit:: Linking Vars>:

            -> `.assign()`
                :: assign varialbe an actual value/number

            -> `.batch_assign()`
                :: create batch job with different sets
                of values assign to each variable.


        - Possible Next <Compile>:

            -> `.quera()`
                :: Compile current program to QuEra job

            -> `.braket()`
                :: Compile current program to Amazon Braket job

            -> `.braket_local_simulator()`
                :: Compile current program to local simulator job



        """
        return PythonFn(self, fn, duration)


class WaveformTerminate(Waveform, Terminate):
    pass


class Sliceable:
    def slice(
        self, start: Optional[ScalarType] = None, stop: Optional[ScalarType] = None
    ):
        """
        Slice current waveform

        Possible Next:

        - Possible Next <Location>:

            -> `.location(int)`
                :: continue building the waveform sequence,
                Addressing another location

        - Possible Next <WaveForm:: current>:

            -> `.record(str)`
                :: record the value of waveform at current time

        - Possible Next <WaveForm:: append>:

            -> `.linear()`

            -> `.constant()`

            -> `.ploy()`

            -> `.apply()`

            -> `.piecewise_linear()`

            -> `.piecewise_constant()`

            -> `.fn()`

        - Possible Next <LevelCoupling>:

            -> `.rydberg`
                :: Switch to specify rydberg level coupling channel

            -> `.hyperfine`
                :: Switch to specify hyperfine level coupling channel

        - Possible Next <Emit:: Linking Vars>:

            -> `.assign()`
                :: assign varialbe an actual value/number

            -> `.batch_assign()`
                :: create batch job with different sets
                of values assign to each variable.

        - Possible Next <Compile>:

            -> `.quera()`
                :: Compile current program to QuEra job

            -> `.braket()`
                :: Compile current program to Amazon Braket job

            -> `.braket_local_simulator()`
                :: Compile current program to local simulator job

        """
        return Slice(self, start, stop)


class Recordable:
    def record(self, name: str):
        """
        Record the value of the current waveform to a variable.

        Possible Next:

        - Possible Next <Location>:

            -> `.location(int)`
                :: continue building the waveform sequence,
                Addressing another location

        - Possible Next <WaveForm:: current>:

            -> `.slice()`
                :: slice the current waveform

            -> `.record(str)`
                :: record the value of waveform at current time

        - Possible Next <WaveForm:: append>:

            -> `.linear()`

            -> `.constant()`

            -> `.ploy()`

            -> `.apply()`

            -> `.piecewise_linear()`

            -> `.piecewise_constant()`

            -> `.fn()`

        - Possible Next <LevelCoupling>:

            -> `.rydberg`
                :: Switch to specify rydberg level coupling channel

            -> `.hyperfine`
                :: Switch to specify hyperfine level coupling channel

        - Possible Next <Emit:: Linking Vars>:

            -> `.assign()`
                :: assign varialbe an actual value/number

            -> `.batch_assign()`
                :: create batch job with different sets
                of values assign to each variable.

        - Possible Next <Compile>:

            -> `.quera()`
                :: Compile current program to QuEra job

            -> `.braket()`
                :: Compile current program to Amazon Braket job

            -> `.braket_local_simulator()`
                :: Compile current program to local simulator job


        """
        return Record(self, name)


class Apply(Sliceable, Recordable, WaveformTerminate):
    def __init__(self, builder: Builder, wf: ir.Waveform) -> None:
        super().__init__(builder)
        self._waveform = wf


class Linear(Sliceable, Recordable, WaveformTerminate):
    def __init__(
        self, parent: Builder, start: float, stop: float, duration: str
    ) -> None:
        super().__init__(parent)
        self._waveform = ir.Linear(start, stop, duration)


class Constant(Sliceable, Recordable, WaveformTerminate):
    def __init__(self, parent: Builder, value: float, duration: str) -> None:
        super().__init__(parent)
        self._waveform = ir.Constant(value, duration)


class Poly(Sliceable, Recordable, WaveformTerminate):
    def __init__(self, parent: Builder, coeffs: list, duration: str) -> None:
        super().__init__(parent)
        self._waveform = ir.Poly(coeffs, duration)


class PythonFn(Sliceable, Recordable, WaveformTerminate):
    def __init__(self, parent: Builder, fn: Callable, duration: str) -> None:
        super().__init__(parent)
        self._waveform = ir.PythonFn(fn, duration)

    def sample(
        self,
        dt: ScalarType,
        interpolation: Optional[Union[ir.Interpolation, str]] = None,
    ) -> "Sample":
        # """sample the current waveform at the specified time interval."""
        if interpolation is not None:
            return Sample(self, dt, interpolation=interpolation)

        match self.__build_cache__.field_name:
            case ir.control.pulse.rabi.amplitude | ir.control.pulse.detuning:
                return Sample(self, dt, interpolation=ir.Interpolation.Linear)
            case ir.control.pulse.rabi.phase:
                return Sample(self, dt, interpolation=ir.Interpolation.Constant)
            case _:
                raise NotImplementedError(
                    f"Sampling for {self.__build_cache__.field_name} is not implemented"
                )


class Sample(Sliceable, Recordable, WaveformTerminate):
    def __init__(
        self,
        parent: Builder,
        dt: ScalarType,
        interpolation: Union[ir.Interpolation, str],
    ) -> None:
        super().__init__(parent)
        self._dt = ir.cast(dt)
        self._interpolation = ir.Interpolation(interpolation)


class Slice(Recordable, WaveformTerminate):  # slice should not be sliceable
    def __init__(
        self,
        parent: Builder,
        start: Optional[ScalarType] = None,
        stop: Optional[ScalarType] = None,
    ) -> None:
        super().__init__(parent)
        self._start = ir.cast(start) if start is not None else None
        self._stop = ir.cast(stop) if stop is not None else None


class Record(WaveformTerminate):  # record should not be sliceable
    def __init__(
        self,
        parent: Builder,
        name: str,
    ) -> None:
        super().__init__(parent)
        self._name = name
