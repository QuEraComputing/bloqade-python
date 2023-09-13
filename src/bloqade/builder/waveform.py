from functools import reduce
from bloqade.builder.base import Builder
from bloqade.builder.typing import ScalarType
from bloqade.builder.route import WaveformRoute

from beartype import beartype
from beartype.typing import Optional, Union, List, Callable

import bloqade.ir as ir


class WaveformAttachable(Builder):
    @beartype
    def linear(
        self, start: ScalarType, stop: ScalarType, duration: ScalarType
    ) -> "Linear":
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
                :: creating new channel to address another location(s)

        - Possible Next <WaveForm:: current>:

            -> `.slice()`
                :: slice current waveform

            -> `.record(str)`
                :: record the value of waveform at current time

        - Possible Next <WaveForm:: append>:

            :: Append waveform into current channel

            -> `.linear()`

            -> `.constant()`

            -> `.ploy()`

            -> `.apply()`

            -> `.piecewise_linear()`

            -> `.piecewise_constant()`

            -> `.fn()`

        - Possible Next <LevelCoupling>:

            -> `.rydberg`
                :: Create/Switch to new rydberg level coupling channel

            -> `.hyperfine`
                :: Create/Switch to new hyperfine level coupling channel

        - Possible Next <Emit:: Linking Vars>:

            -> `.assign()`
                :: assign varialbe an actual value/number

            -> `.batch_assign()`
                :: create batch job with different
                sets of values assign to each variable.

        - Possible Next <Backend>:

            -> `.quera`
                :: specify QuEra backend

            -> `.braket`
                :: specify QuEra backend

        """
        return Linear(start, stop, duration, self)

    @beartype
    def constant(self, value: ScalarType, duration: ScalarType) -> "Constant":
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
                :: creating new channel to address another location(s)

        - Possible Next <WaveForm:: current>:

            -> `.slice()`
                :: slice current waveform

            -> `.record(str)`
                :: record the value of waveform at current time

        - Possible Next <WaveForm:: append>:

            :: Append waveform into current channel

            -> `.linear()`

            -> `.constant()`

            -> `.ploy()`

            -> `.apply()`

            -> `.piecewise_linear()`

            -> `.piecewise_constant()`

            -> `.fn()`

        - Possible Next <LevelCoupling>:

            -> `.rydberg`
                :: Create/Switch to new rydberg level coupling channel

            -> `.hyperfine`
                :: Create/Switch to new hyperfine level coupling channel

        - Possible Next <Emit:: Linking Vars>:

            -> `.assign()`
                :: assign varialbe an actual value/number

            -> `.batch_assign()`
                :: create batch job with different sets
                of values assign to each variable.

        - Possible Next <Backend>:

            -> `.quera`
                :: specify QuEra backend

            -> `.braket`
                :: specify QuEra backend

        """
        return Constant(value, duration, self)

    @beartype
    def poly(self, coeffs: List[ScalarType], duration: ScalarType) -> "Poly":
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
                :: creating new channel to address another location(s)

        - Possible Next <WaveForm:: current>:

            -> `.slice()`
                :: slice current waveform

            -> `.record(str)`
                :: record the value of waveform at current time

        - Possible Next <WaveForm:: append>:

            :: Append waveform into current channel

            -> `.linear()`

            -> `.constant()`

            -> `.ploy()`

            -> `.apply()`

            -> `.piecewise_linear()`

            -> `.piecewise_constant()`

            -> `.fn()`

        - Possible Next <LevelCoupling>:

            -> `.rydberg`
                :: Create/Switch to new rydberg level coupling channel

            -> `.hyperfine`
                :: Create/Switch to new hyperfine level coupling channel


        - Possible Next <Emit:: Linking Vars>:

            -> `.assign()`
                :: assign varialbe an actual value/number

            -> `.batch_assign()`
                :: create batch job with different sets
                of values assign to each variable.

        - Possible Next <Backend>:

            -> `.quera`
                :: specify QuEra backend

            -> `.braket`
                :: specify QuEra backend

        """
        return Poly(coeffs, duration, self)

    @beartype
    def apply(self, wf: ir.Waveform) -> "Apply":
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
                :: creating new channel to address another location(s)

        - Possible Next <WaveForm:: current>:

            -> `.slice()`
                :: slice current waveform

            -> `.record(str)`
                :: record the value of waveform at current time

        - Possible Next <WaveForm:: append>:

            :: Append waveform into current channel

            -> `.linear()`

            -> `.constant()`

            -> `.ploy()`

            -> `.apply()`

            -> `.piecewise_linear()`

            -> `.piecewise_constant()`

            -> `.fn()`

        - Possible Next <LevelCoupling>:

            -> `.rydberg`
                :: Create/Switch to new rydberg level coupling channel

            -> `.hyperfine`
                :: Create/Switch to new hyperfine level coupling channel


        - Possible Next <Emit:: Linking Vars>:

            -> `.assign()`
                :: assign varialbe an actual value/number

            -> `.batch_assign()`
                :: create batch job with different sets
                of values assign to each variable.

        - Possible Next <Backend>:

            -> `.quera`
                :: specify QuEra backend

            -> `.braket`
                :: specify QuEra backend

        """
        return Apply(wf, self)

    @beartype
    def piecewise_linear(
        self, durations: List[ScalarType], values: List[ScalarType]
    ) -> "PiecewiseLinear":
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
                :: creating new channel to address another location(s)

        - Possible Next <WaveForm:: current>:

            -> `.slice()`
                :: slice current waveform

            -> `.record(str)`
                :: record the value of waveform at current time

        - Possible Next <WaveForm:: append>:

            :: Append waveform into current channel

            -> `.linear()`

            -> `.constant()`

            -> `.ploy()`

            -> `.apply()`

            -> `.piecewise_linear()`

            -> `.piecewise_constant()`

            -> `.fn()`

        - Possible Next <LevelCoupling>:

            -> `.rydberg`
                :: Create/Switch to new rydberg level coupling channel

            -> `.hyperfine`
                :: Create/Switch to new hyperfine level coupling channel


        - Possible Next <Emit:: Linking Vars>:

            -> `.assign()`
                :: assign varialbe an actual value/number

            -> `.batch_assign()`
                :: create batch job with different sets
                of values assign to each variable.

        - Possible Next <Backend>:

            -> `.quera`
                :: specify QuEra backend

            -> `.braket`
                :: specify QuEra backend

        """
        return PiecewiseLinear(durations, values, self)

    @beartype
    def piecewise_constant(
        self, durations: List[ScalarType], values: List[ScalarType]
    ) -> "PiecewiseConstant":
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
                :: creating new channel to address another location(s)

        - Possible Next <WaveForm:: current>:

            -> `.slice()`
                :: slice current waveform

            -> `.record(str)`
                :: record the value of waveform at current time

        - Possible Next <WaveForm:: append>:

            :: Append waveform into current channel

            -> `.linear()`

            -> `.constant()`

            -> `.ploy()`

            -> `.apply()`

            -> `.piecewise_linear()`

            -> `.piecewise_constant()`

            -> `.fn()`

        - Possible Next <LevelCoupling>:

            -> `.rydberg`
                :: Create/Switch to new rydberg level coupling channel

            -> `.hyperfine`
                :: Create/Switch to new hyperfine level coupling channel


        - Possible Next <Emit:: Linking Vars>:

            -> `.assign()`
                :: assign varialbe an actual value/number

            -> `.batch_assign()`
                :: create batch job with different sets
                of values assign to each variable.


        - Possible Next <Backend>:

            -> `.quera`
                :: specify QuEra backend

            -> `.braket`
                :: specify QuEra backend

        """
        return PiecewiseConstant(durations, values, self)

    @beartype
    def fn(self, fn: Callable, duration: ScalarType) -> "Fn":
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
                :: creating new channel to address another location(s)

        - Possible Next <WaveForm:: current>:

            -> `.slice()`
                :: slice current waveform

            -> `.record(str)`
                :: record the value of waveform at current time

            -> `.sample()`
                :: sample current callable at given time points

        - Possible Next <WaveForm:: append>:

            :: Append waveform into current channel

            -> `.linear()`

            -> `.constant()`

            -> `.ploy()`

            -> `.apply()`

            -> `.piecewise_linear()`

            -> `.piecewise_constant()`

            -> `.fn()`

        - Possible Next <LevelCoupling>:

            -> `.rydberg`
                :: Create/Switch to new rydberg level coupling channel

            -> `.hyperfine`
                :: Create/Switch to new hyperfine level coupling channel


        - Possible Next <Emit:: Linking Vars>:

            -> `.assign()`
                :: assign varialbe an actual value/number

            -> `.batch_assign()`
                :: create batch job with different sets
                of values assign to each variable.


        - Possible Next <Backend>:

            -> `.quera`
                :: specify QuEra backend

            -> `.braket`
                :: specify QuEra backend

        """
        return Fn(fn, duration, self)


# NOTE: waveform can refer previous pulse notes
#       or continue to specify pragma options
class Waveform(WaveformRoute, WaveformAttachable):
    pass


# mixin for slice and record
class Slicible:
    @beartype
    def slice(
        self,
        start: Optional[ScalarType] = None,
        stop: Optional[ScalarType] = None,
    ) -> "Slice":
        """
        Slice current waveform

        Possible Next:

        - Possible Next <Location>:

            -> `.location(int)`
                :: creating new channel to address
                another location(s)

        - Possible Next <WaveForm:: current>:

            -> `.record(str)`
                :: record the value of waveform at current time

        - Possible Next <WaveForm:: append>:

            :: Append waveform into current channel

            -> `.linear()`

            -> `.constant()`

            -> `.ploy()`

            -> `.apply()`

            -> `.piecewise_linear()`

            -> `.piecewise_constant()`

            -> `.fn()`

        - Possible Next <LevelCoupling>:

            -> `.rydberg`
                :: Create/Switch to new rydberg level coupling channel

            -> `.hyperfine`
                :: Create/Switch to new hyperfine level coupling channel


        - Possible Next <Emit:: Linking Vars>:

            -> `.assign()`
                :: assign varialbe an actual value/number

            -> `.batch_assign()`
                :: create batch job with different sets
                of values assign to each variable.


        - Possible Next <Backend>:

            -> `.quera`
                :: specify QuEra backend

            -> `.braket`
                :: specify QuEra backend
        """
        return Slice(start, stop, self)


class Recordable:
    @beartype
    def record(self, name: str) -> "Record":
        """
        Record the value of the current waveform to a variable.

        Possible Next:

        - Possible Next <Location>:

            -> `.location(int)`
                :: creating new channel to address
                another location(s)

        - Possible Next <WaveForm:: current>:

            -> `.slice()`
                :: slice the current waveform

            -> `.record(str)`
                :: record the value of waveform at current time

        - Possible Next <WaveForm:: append>:

            :: Append waveform into current channel

            -> `.linear()`

            -> `.constant()`

            -> `.ploy()`

            -> `.apply()`

            -> `.piecewise_linear()`

            -> `.piecewise_constant()`

            -> `.fn()`

        - Possible Next <LevelCoupling>:

            -> `.rydberg`
                :: Create/Switch to new rydberg level coupling channel

            -> `.hyperfine`
                :: Create/Switch to new hyperfine level coupling channel

        - Possible Next <Emit:: Linking Vars>:

            -> `.assign()`
                :: assign varialbe an actual value/number

            -> `.batch_assign()`
                :: create batch job with different sets
                of values assign to each variable.

        - Possible Next <Backend>:

            -> `.quera`
                :: specify QuEra backend

            -> `.braket`
                :: specify QuEra backend

        """
        return Record(name, self)


class WaveformPrimitive(Waveform, Slicible, Recordable):
    def __bloqade_ir__(self):
        raise NotImplementedError


class Linear(WaveformPrimitive):
    __match_args__ = ("_start", "_stop", "_duration", "__parent__")

    def __init__(
        self,
        start: ScalarType,
        stop: ScalarType,
        duration: ScalarType,
        parent: Optional[Builder] = None,
    ) -> None:
        super().__init__(parent)
        self._start = ir.cast(start)
        self._stop = ir.cast(stop)
        self._duration = ir.cast(duration)

    def __bloqade_ir__(self) -> ir.Linear:
        return ir.Linear(start=self._start, stop=self._stop, duration=self._duration)


class Constant(WaveformPrimitive):
    __match_args__ = ("_value", "_duration", "__parent__")

    def __init__(
        self, value: ScalarType, duration: ScalarType, parent: Optional[Builder] = None
    ) -> None:
        super().__init__(parent)
        self._value = ir.cast(value)
        self._duration = ir.cast(duration)

    def __bloqade_ir__(self) -> ir.Constant:
        return ir.Constant(value=self._value, duration=self._duration)


class Poly(WaveformPrimitive):
    __match_args__ = ("_coeffs", "_duration", "__parent__")

    def __init__(
        self,
        coeffs: List[ScalarType],
        duration: ScalarType,
        parent: Optional[Builder] = None,
    ) -> None:
        super().__init__(parent)
        self._coeffs = ir.cast(coeffs)
        self._duration = ir.cast(duration)

    def __bloqade_ir__(self):
        return ir.Poly(coeffs=self._coeffs, duration=self._duration)


class Apply(WaveformPrimitive):
    __match_args__ = ("_wf", "__parent__")

    def __init__(self, wf: ir.Waveform, parent: Optional[Builder] = None):
        super().__init__(parent)
        self._wf = wf

    def __bloqade_ir__(self):
        return self._wf


class PiecewiseLinear(WaveformPrimitive):
    __match_args__ = ("_durations", "_values", "__parent__")

    def __init__(
        self,
        durations: List[ScalarType],
        values: List[ScalarType],
        parent: Optional[Builder] = None,
    ):
        assert (
            len(durations) == len(values) - 1
        ), "durations and values must be the same length"

        super().__init__(parent)
        self._durations = list(map(ir.cast, durations))
        self._values = list(map(ir.cast, values))

    def __bloqade_ir__(self):
        iter = zip(self._values[:-1], self._values[1:], self._durations)
        wfs = [ir.Linear(start=v0, stop=v1, duration=t) for v0, v1, t in iter]

        return reduce(lambda a, b: a.append(b), wfs)


class PiecewiseConstant(WaveformPrimitive):
    __match_args__ = ("_durations", "_values", "__parent__")

    def __init__(
        self,
        durations: List[ScalarType],
        values: List[ScalarType],
        parent: Optional[Builder] = None,
    ) -> None:
        assert len(durations) == len(
            values
        ), "durations and values must be the same length"
        super().__init__(parent)
        self._durations = list(map(ir.cast, durations))
        self._values = list(map(ir.cast, values))

    def __bloqade_ir__(self):
        iter = zip(self._values, self._durations)
        wfs = [ir.Constant(value=v, duration=t) for v, t in iter]
        return reduce(lambda a, b: a.append(b), wfs)


class Fn(WaveformPrimitive):
    __match_args__ = ("_fn", "_duration", "__parent__")

    def __init__(
        self,
        fn: Callable,
        duration: ScalarType,
        parent: Optional[Builder] = None,
    ) -> None:
        super().__init__(parent)
        self._fn = fn
        self._duration = ir.cast(duration)

    @beartype
    def sample(
        self, dt: ScalarType, interpolation: Union[ir.Interpolation, str, None] = None
    ):
        return Sample(dt, interpolation, self)

    def __bloqade_ir__(self):
        return ir.PythonFn(self._fn, self._duration)


# NOTE: no double-slice or double-record
class Slice(Waveform, Recordable):
    __match_args__ = ("_start", "_stop", "__parent__")

    def __init__(
        self,
        start: Optional[ScalarType] = None,
        stop: Optional[ScalarType] = None,
        parent: Optional[Builder] = None,
    ) -> None:
        super().__init__(parent)
        # NOTE: this should no raise for None
        self._start = ir.scalar.trycast(start)
        self._stop = ir.scalar.trycast(stop)


class Record(Waveform, Slicible):  # record should not be sliceable
    __match_args__ = ("_name", "__parent__")

    def __init__(
        self,
        name: str,
        parent: Optional[Builder] = None,
    ) -> None:
        super().__init__(parent)
        self._name = ir.var(name)


class Sample(Slicible, Recordable, WaveformRoute):
    __match_args__ = ("_dt", "_interpolation", "__parent__")

    def __init__(
        self,
        dt: ScalarType,
        interpolation: Union[ir.Interpolation, str, None],
        parent: Builder,
    ) -> None:
        super().__init__(parent)
        self._dt = ir.cast(dt)
        if interpolation is None:
            self._interpolation = None
        else:
            self._interpolation = ir.Interpolation(interpolation)
