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

        Append or assign a linear waveform to the current location(s).

        If you specified a spatial modulation (e.g. `uniform`, `location`,`var`)
        previously without a waveform you will now have completed the construction
        of a "drive", one or a sum of drives creating a "field"
        (e.g. Real-valued Rabi Amplitude/Phase).

        If you have already specified a waveform previously you will now be appending
        this waveform to that previous waveform.

        Usage Example:
        ```
        >>> prog = start.add_position((0,0)).rydberg.detuning.uniform
        # apply a linear waveform that goes from 0 to 1 radians/us in 0.5 us
        >>> prog.linear(start=0,stop=1,duration=0.5)
        ```

        - Your next steps include:
        - Continue building your waveform via:
            - |_ `...linear(start, stop, duration).linear(start, stop, duration)`:
                to append another linear waveform
            - |_ `...linear(start, stop, duration).constant(value, duration)`:
                to append a constant waveform
            - |_ `...linear(start, stop, duration)
                .piecewise_linear([durations], [values])`:
                to append a piecewise linear waveform
            - |_ `...linear(start, stop, duration)
                .piecewise_constant([durations], [values])`:
                to append a piecewise constant waveform
            - |_ `...linear(start, stop, duration).poly([coefficients], duration)`:
                to append a polynomial waveform
            - |_ `...linear(start, stop, duration).apply(wf:bloqade.ir.Waveform)`:
                to append a pre-defined waveform
            - |_ `...linear(start, stop, duration).fn(f(t,...))`:
                to append a waveform defined by a python function
        - Slice a portion of the waveform to be used:
            - |_ `...linear(start, stop, duration).slice(start, stop, duration)`
        - Save the ending value of your waveform to be reused elsewhere
            - |_ `...linear(start, stop, duration).record("you_variable_here")`
        - Begin constructing another drive by starting a new spatial modulation
            (this drive will be summed to the one you just created):
            - |_ `...linear(start, stop, duration).uniform`:
                To address all atoms in the field
            - |_ `...linear(start, stop, duration).location(int)`:
                To address an atom at a specific location via index
            - |_ `...linear(start, stop, duration).var(str)`
                - |_ To address an atom at a specific location via variable
                - |_ To address multiple atoms at specific locations by specifying
                    a single variable and then assigning it a list of coordinates
        - Assign values to pre-existing variables via:
            - |_ `...linear(start, stop, duration).assign(variable_name = value)`:
                to assign a single value to a variable
            - |_ `...linear(start, stop, duration)
                .batch_assign(variable_name = [value1, ...])`:
                to assign multiple values to a variable
            - |_ `...linear(start, stop, duration).args(["previously_defined_var"])`:
                to defer assignment of a variable to execution time
        - Select the backend you want your program to run on via:
            - |_ `...linear(start, stop, duration).braket`:
                to run on Braket local emulator or QuEra hardware remotely
            - |_ `...linear(start, stop, duration).bloqade`:
                to run on the Bloqade local emulator
            - |_ `...linear(start, stop, duration).device`:
                to specify the backend via string
        - Choose to parallelize your atom geometry,
          duplicating it to fill the whole space:
            - |_ `...linear(start, stop, duration).parallelize(spacing)`
        - Start targeting another level coupling
            - |_ `...linear(start, stop, duration).rydberg`:
                to target the Rydberg level coupling
            - |_ `...linear(start, stop, duration).hyperfine`:
                to target the Hyperfine level coupling
        - Start targeting other fields within your current level coupling
          (previously selected as `rydberg` or `hyperfine`):
            - |_ `...linear(start, stop, duration).amplitude`:
                to target the real-valued Rabi Amplitude field
            - |_ `...linear(start, stop, duration).phase`:
                to target the real-valued Rabi Phase field
            - |_ `...linear(start, stop, duration).detuning`:
                to target the Detuning field
            - |_ `...linear(start, stop, duration).rabi`:
                to target the complex-valued Rabi field
        """

        return Linear(start, stop, duration, self)

    @beartype
    def constant(self, value: ScalarType, duration: ScalarType) -> "Constant":
        """
        Append or assign a constant waveform to the current location(s).

        If you specified a spatial modulation (e.g. `uniform`, `location`,`var`)
        previously without a waveform you will now have completed the construction
        of a "drive", one or a sum of drives creating a "field"
        (e.g. Real-valued Rabi Amplitude/Phase).

        If you have already specified a waveform previously you will now be appending
        this waveform to that previous waveform.

        Usage Example:
        ```
        >>> prog = start.add_position((0,0)).rydberg.detuning.uniform
        # apply a constant waveform of 1.9 radians/us for 0.5 us
        >>> prog.constant(value=1.9,duration=0.5)
        ```

        - Your next steps include:
        - Continue building your waveform via:
            - |_ `...constant(value, duration).linear(start, stop, duration)`:
                to append another linear waveform
            - |_ `...constant(value, duration).constant(value, duration)`:
                to append a constant waveform
            - |_ `...constant(value, duration)
                .piecewise_linear([durations], [values])`:
                to append a piecewise linear waveform
            - |_ `...constant(value, duration)
                .piecewise_constant([durations], [values])`:
                to append a piecewise constant waveform
            - |_ `...constant(value, duration).poly([coefficients], duration)`:
                to append a polynomial waveform
            - |_ `...constant(value, duration).apply(wf:bloqade.ir.Waveform)`:
                to append a pre-defined waveform
            - |_ `...constant(value, duration).fn(f(t,...))`:
                to append a waveform defined by a python function
        - Slice a portion of the waveform to be used:
            - |_ `...constant(value, duration).slice(start, stop, duration)`
        - Save the ending value of your waveform to be reused elsewhere
            - |_ `...constant(value, duration).record("you_variable_here")`
        - Begin constructing another drive by starting a new spatial modulation
            (this drive will be summed to the one you just created):
            -|_ `...constant(value, duration).uniform`:
                To address all atoms in the field
            -|_ `...constant(value, duration).var`:
                To address an atom at a specific location via index
            -|_ `...constant(value, duration).location(int)`
                - |_ To address an atom at a specific location via variable
                - |_ To address multiple atoms at specific locations by specifying
                    a single variable and then assigning it a list of coordinates
        - Assign values to pre-existing variables via:
            - |_ `...constant(value, duration).assign(variable_name = value)`:
                to assign a single value to a variable
            - |_ `...constant(value, duration)
                .batch_assign(variable_name = [value1, ...])`:
                to assign multiple values to a variable
            - |_ `...constant(value, duration).args(["previously_defined_var"])`:
                to defer assignment of a variable to execution time
        - Select the backend you want your program to run on via:
            - |_ `...constant(value, duration).braket`:
                to run on Braket local emulator or QuEra hardware remotely
            - |_ `...constant(value, duration).bloqade`:
                to run on the Bloqade local emulator
            - |_ `...constant(value, duration).device`:
                to specify the backend via string
        - Choose to parallelize your atom geometry,
          duplicating it to fill the whole space:
            - |_ `...constant(start, stop, duration).parallelize(spacing)`
        - Start targeting another level coupling
            - |_ `...constant(value, duration).rydberg`:
                to target the Rydberg level coupling
            - |_ `...constant(value, duration).hyperfine`:
                to target the Hyperfine level coupling
        - Start targeting other fields within your current
          level coupling (previously selected as `rydberg` or `hyperfine`):
            - |_ `...constant(value, duration).amplitude`:
                to target the real-valued Rabi Amplitude field
            - |_ `...constant(value, duration).phase`:
                to target the real-valued Rabi Phase field
            - |_ `...constant(value, duration).detuning`:
                to target the Detuning field
            - |_ `...constant(value, duration).rabi`:
                to target the complex-valued Rabi field

        """
        return Constant(value, duration, self)

    @beartype
    def poly(self, coeffs: List[ScalarType], duration: ScalarType) -> "Poly":
        """
        Append or assign a waveform with a polynomial profile to current location(s).

        You pass in a list of coefficients and a duration to this method which obeys
        the following expression:

        `
        wv(t) = coeffs[0] + coeffs[1]*t + coeffs[2]*t^2 + ... + coeffs[n]*t^n
        `

        If you specified a spatial modulation (e.g. `uniform`, `location`,`var`)
        previously without a waveform you will now have completed the construction
        of a "drive", one or a sum of drives creating a "field"
        (e.g. Real-valued Rabi Amplitude/Phase).

        If you have already specified a waveform previously you will now be appending
        this waveform to that previous waveform.

        Usage Example:
        ```
        >>> prog = start.add_position((0,0)).rydberg.detuning.uniform
        >>> coeffs = [-1, 0.5, 1.2]
        # resulting polynomial is:
        # f(t) = -1 + 0.5*t + 1.2*t^2 with duration of
        # 0.5 us
        >>> prog.poly(coeffs, duration=0.5)
        ```

        - Your next steps include:
        - Continue building your waveform via:
            - |_ `...poly([coeffs], duration).linear(start, stop, duration)`:
                to append another linear waveform
            - |_ `...poly([coeffs], duration).constant(value, duration)`:
                to append a constant waveform
            - |_ `...poly([coeffs], duration)
                .piecewise_linear([durations], [values])`:
                to append a piecewise linear waveform
            - |_ `...poly([coeffs], duration)
                .piecewise_constant([durations],[values])`:
                to append a piecewise constant waveform
            - |_ `...poly([coeffs], duration).poly([coefficients], duration)`:
                to append a polynomial waveform
            - |_ `...poly([coeffs], duration).apply(waveform)`:
                to append a pre-defined waveform
            - |_ `...poly([coeffs], duration).fn(f(t,...))`:
                to append a waveform defined by a python function
        - Slice a portion of the waveform to be used:
            - |_ `...poly([coeffs], duration).slice(start, stop, duration)`
        - Save the ending value of your waveform to be reused elsewhere
            - |_ `...poly([coeffs], duration).record("you_variable_here")`
        - Begin constructing another drive by starting a new spatial modulation
          (this drive will be summed to the one you just created):
            -|_ `...poly([coeffs], duration).uniform`:
                To address all atoms in the field
            -|_ `...poly([coeffs], duration).location(int)`:
                To address an atom at a specific location via index
            -|_ `...poly([coeffs], duration).var(str)`
                - |_ To address an atom at a specific location via variable
                - |_ To address multiple atoms at specific locations by
                    specifying a single variable and then assigning
                    it a list of coordinates
        - Assign values to pre-existing variables via:
            - |_ `...poly([coeffs], duration).assign(variable_name = value)`:
                to assign a single value to a variable
            - |_ `...poly([coeffs], duration)
                .batch_assign(variable_name = [value1, ...])`:
                to assign multiple values to a variable
            - |_ `...poly([coeffs], duration).args(["previously_defined_var"])`:
                to defer assignment of a variable to execution time
        - Select the backend you want your program to run on via:
            - |_ `...poly([coeffs], duration).braket`:
                to run on Braket local emulator or QuEra hardware remotely
            - |_ `...poly([coeffs], duration).bloqade`:
                to run on the Bloqade local emulator
            - |_ `...poly([coeffs], duration).device`:
                to specify the backend via string
        - Choose to parallelize your atom geometry,
          duplicating it to fill the whole space:
            - |_ `...poly([coeffs], duration).parallelize(spacing)`
        - Start targeting another level coupling
            - |_ `...poly([coeffs], duration).rydberg`:
                to target the Rydberg level coupling
            - |_ `...poly([coeffs], duration).hyperfine`:
                to target the Hyperfine level coupling
        - Start targeting other fields within your current level
          coupling (previously selected as `rydberg` or `hyperfine`):
            - |_ `...poly([coeffs], duration).amplitude`:
                to target the real-valued Rabi Amplitude field
            - |_ `...poly([coeffs], duration).phase`:
                to target the real-valued Rabi Phase field
            - |_ `...poly([coeffs], duration).detuning`:
                to target the Detuning field
            - |_ `...poly([coeffs], duration).rabi`:
                to target the complex-valued Rabi field
        """
        return Poly(coeffs, duration, self)

    @beartype
    def apply(self, wf: ir.Waveform) -> "Apply":
        """
        Apply a [`Waveform`][bloqade.ir.control.Waveform] built previously to
        current location(s).

        If you specified a spatial modulation (e.g. `uniform`, `location`,`var`)
        previously without a waveform you will now have completed the construction
        of a "drive", one or a sum of drives creating a "field"
        (e.g. Real-valued Rabi Amplitude/Phase).

        If you have already specified a waveform previously you will now be appending
        this waveform to that previous waveform.

        Usage Example:
        ```
        >>> prog = start.add_position((0,0)).rydberg.detuning.uniform
        # build our waveform independently of the main program
        >>> from bloqade import piecewise_linear
        >>> wf = piecewise_linear(durations=[0.3, 2.5, 0.3],
        values=[0.0, 2.0, 2.0, 0.0])
        >>> prog.apply(wf)
        ```

        - Your next steps include:
        - Continue building your waveform via:
            - |_ `...apply(waveform).linear(start, stop, duration)`:
                to append another linear waveform
            - |_ `...apply(waveform).constant(value, duration)`:
                to append a constant waveform
            - |_ `...apply(waveform).piecewise_linear([durations], [values])`:
                to append a piecewise linear waveform
            - |_ `...apply(waveform).piecewise_constant([durations], [values])`:
                to append a piecewise constant waveform
            - |_ `...apply(waveform).poly([coefficients], duration)`:
                to append a polynomial waveform
            - |_ `...apply(waveform).apply(waveform)`:
                to append a pre-defined waveform
            - |_ `...apply(waveform).fn(f(t,...))`:
                to append a waveform defined by a python function
        - Slice a portion of the waveform to be used:
            - |_ `...apply(waveform).slice(start, stop, duration)`
        - Save the ending value of your waveform to be reused elsewhere
            - |_ `...apply(waveform).record("you_variable_here")`
        - Begin constructing another drive by starting a new spatial modulation
          (this drive will be summed to the one you just created):
            -|_ `...apply(waveform).uniform`: To address all atoms in the field
            -|_ `...apply(waveform).location(int)`:
                To address an atom at a specific location via index
            -|_ `...apply(waveform).var(str)`
                - |_ To address an atom at a specific location via variable
                - |_ To address multiple atoms at specific locations by specifying a
                    single variable and then assigning it a list of coordinates
        - Assign values to pre-existing variables via:
            - |_ `...apply(waveform).assign(variable_name = value)`:
                to assign a single value to a variable
            - |_ `...apply(waveform).batch_assign(variable_name = [value1, ...])`:
                to assign multiple values to a variable
            - |_ `...apply(waveform).args(["previously_defined_var"])`:
                to defer assignment of a variable to execution time
        - Select the backend you want your program to run on via:
            - |_ `...apply(waveform).braket`:
                to run on Braket local emulator or QuEra hardware remotely
            - |_ `...apply(waveform).bloqade`:
                to run on the Bloqade local emulator
            - |_ `...apply(waveform).device`:
                to specify the backend via string
        - Choose to parallelize your atom geometry,
          duplicating it to fill the whole space:
            - |_ `...apply(waveform).parallelize(spacing)`
        - Start targeting another level coupling
            - |_ `...apply(waveform).rydberg`: to target the Rydberg level coupling
            - |_ `...apply(waveform).hyperfine`: to target the Hyperfine level coupling
        - Start targeting other fields within your current level coupling
          (previously selected as `rydberg` or `hyperfine`):
            - |_ `...apply(waveform).amplitude`:
                to target the real-valued Rabi Amplitude field
            - |_ `...apply(waveform).phase`:
                to target the real-valued Rabi Phase field
            - |_ `...apply(waveform).detuning`:
                to target the Detuning field
            - |_ `...apply(waveform).rabi`:
                to target the complex-valued Rabi field
        """
        return Apply(wf, self)

    @beartype
    def piecewise_linear(
        self, durations: List[ScalarType], values: List[ScalarType]
    ) -> "PiecewiseLinear":
        """
        Append or assign a piecewise linear waveform to current location(s),
        where the waveform is formed by connecting `values[i], values[i+1]`
        with linear segments.

        The `durations` argument should have # of elements = len(values) - 1.
        `durations` should be the duration PER section of the waveform, NON-CUMULATIVE.

        If you specified a spatial modulation (e.g. `uniform`, `location`,`var`)
        previously without a waveform you will now have completed the construction
        of a "drive", one or a sum of drives creating a "field"
        (e.g. Real-valued Rabi Amplitude/Phase).

        If you have already specified a waveform previously you will now be appending
        this waveform to that previous waveform.

        Usage Example:
        ```
        >>> prog = start.add_position((0,0)).rydberg.detuning.uniform
        # ramp our waveform up to a certain value, hold it
        # then ramp down. In this case, we ramp up to 2.0 rad/us in 0.3 us,
        # then hold it for 1.5 us before ramping down in 0.3 us back to 0.0 rad/us.
        >>> prog.piecewise_linear(durations=[0.3, 2.0, 0.3],
        values=[0.0, 2.0, 2.0, 0.0])
        ```

        - Your next steps include:
        - Continue building your waveform via:
            - |_ `...piecewise_linear([durations], [values])
                .linear(start, stop, duration)`:
                to append another linear waveform
            - |_ `...piecewise_linear([durations], [values]).constant(value, duration)`:
                to append a constant waveform
            - |_ `...piecewise_linear([durations], [values])
                .piecewise_linear(durations, values)`:
                to append a piecewise linear waveform
            - |_ `...piecewise_linear([durations], [values])
                .piecewise_constant([durations], [values])`:
                to append a piecewise constant waveform
            - |_ `...piecewise_linear([durations], [values])
                .poly([coefficients], duration)`: to append a polynomial waveform
            - |_ `...piecewise_linear([durations], [values]).apply(waveform)`:
                to append a pre-defined waveform
            - |_ `...piecewise_linear([durations], [values]).fn(f(t,...))`:
                to append a waveform defined by a python function
        - Slice a portion of the waveform to be used:
            - |_ `...piecewise_linear([durations], [values])
                .slice(start, stop, duration)`
        - Save the ending value of your waveform to be reused elsewhere
            - |_ `...piecewise_linear([durations], [values])
                .record("you_variable_here")`
        - Begin constructing another drive by starting a new spatial modulation
          (this drive will be summed to the one you just created):
            -|_ `...piecewise_linear([durations], [values]).uniform`:
                To address all atoms in the field
            -|_ `...piecewise_linear([durations], [values]).var`:
                To address an atom at a specific location via index
            -|_ `...piecewise_linear([durations], [values]).location(int)`
                - |_ To address an atom at a specific location via variable
                - |_ To address multiple atoms at specific locations by
                    specifying a single variable and then assigning it a
                    list of coordinates
        - Assign values to pre-existing variables via:
            - |_ `...piecewise_linear([durations], [values])
                .assign(variable_name = value)`:
                to assign a single value to a variable
            - |_ `...piecewise_linear([durations], [values])
                .batch_assign(variable_name = [value1, ...])`:
                to assign multiple values to a variable
            - |_ `...piecewise_linear([durations], [values])
                .args(["previously_defined_var"])`:
                to defer assignment of a variable to execution time
        - Select the backend you want your program to run on via:
            - |_ `...piecewise_linear([durations], [values]).braket`:
                to run on Braket local emulator or QuEra hardware remotely
            - |_ `...piecewise_linear([durations], [values]).bloqade`:
                to run on the Bloqade local emulator
            - |_ `...piecewise_linear([durations], [values]).device`:
                to specify the backend via string
        - Choose to parallelize your atom geometry,
          duplicating it to fill the whole space:
            - |_ `...piecewise_linear([durations], [values]).parallelize(spacing)`
        - Start targeting another level coupling
            - |_ `...piecewise_linear([durations], [values]).rydberg`:
                to target the Rydberg level coupling
            - |_ `...piecewise_linear([durations], [values]).hyperfine`:
                to target the Hyperfine level coupling
        - Start targeting other fields within your current level coupling
          (previously selected as `rydberg` or `hyperfine`):
            - |_ `...piecewise_linear([durations], [values]).amplitude`:
                to target the real-valued Rabi Amplitude field
            - |_ `...piecewise_linear([durations], [values]).phase`:
                to target the real-valued Rabi Phase field
            - |_ `...piecewise_linear([durations], [values]).detuning`:
                to target the Detuning field
            - |_ `....rabi`: to target the complex-valued Rabi field
        """
        return PiecewiseLinear(durations, values, self)

    @beartype
    def piecewise_constant(
        self, durations: List[ScalarType], values: List[ScalarType]
    ) -> "PiecewiseConstant":
        """
        Append or assign a piecewise constant waveform to current location(s).

        The `durations` argument should have number of elements = len(values).
        `durations` should be the duration PER section of the waveform,
        NON-CUMULATIVE.

        If you specified a spatial modulation (e.g. `uniform`, `location`,`var`)
        previously without a waveform you will now have completed the construction
        of a "drive", one or a sum of drives creating a "field"
        (e.g. Real-valued Rabi Amplitude/Phase).

        If you have already specified a waveform previously you will now be appending
        this waveform to that previous waveform.

        Usage Example:
        ```
        >>> prog = start.add_position((0,0)).rydberg.rabi.phase.uniform
        # create a staircase, we hold 0.0 rad/us for 1.0 us, then
        # to 1.0 rad/us for 0.5 us before stopping at 0.8 rad/us for 0.9 us.
        >>> prog.piecewise_linear(durations=[0.3, 2.0, 0.3], values=[1.0, 0.5, 0.9])
        ```

        - Your next steps including:
        - Continue building your waveform via:
            - |_ `...piecewise_constant([durations], [values])
                .linear(start, stop, duration)`: to append another linear waveform
            - |_ `...piecewise_constant([durations], [values])
                .constant(value, duration)`: to append a constant waveform
            - |_ `...piecewise_constant([durations], [values])
                .piecewise_linear([durations], [values])`:
                to append a piecewise linear waveform
            - |_ `...piecewise_constant([durations], [values])
                .piecewise_constant([durations], [values])`:
                to append a piecewise constant waveform
            - |_ `...piecewise_constant([durations], [values])
                .poly([coefficients], duration)`: to append a polynomial waveform
            - |_ `...piecewise_constant([durations], [values])
                .apply(waveform)`: to append a pre-defined waveform
            - |_ `...piecewise_constant([durations], [values]).fn(f(t,...))`:
                to append a waveform defined by a python function
        - Slice a portion of the waveform to be used:
            - |_ `...piecewise_constant([durations], [values])
                .slice(start, stop, duration)`
        - Save the ending value of your waveform to be reused elsewhere
            - |_ `...piecewise_constant([durations], [values])
                .record("you_variable_here")`
        - Begin constructing another drive by starting a new spatial modulation
          (this drive will be summed to the one you just created):
            -|_ `...piecewise_constant([durations], [values]).uniform`:
                To address all atoms in the field
            -|_ `...piecewise_constant([durations], [values]).location(int)`:
                To address an atom at a specific location via index
            -|_ `...piecewise_constant([durations], [values]).var(str)`
                - |_ To address an atom at a specific location via variable
                - |_ To address multiple atoms at specific locations by
                    specifying a single variable and then assigning it a
                    list of coordinates
        - Assign values to pre-existing variables via:
            - |_ `...piecewise_constant([durations], [values])
                .assign(variable_name = value)`: to assign a single value to a variable
            - |_ `...piecewise_constant([durations], [values])
                .batch_assign(variable_name = [value1, ...])`:
                to assign multiple values to a variable
            - |_ `...piecewise_constant([durations], [values])
                .args(["previously_defined_var"])`: to defer assignment
                of a variable to execution time
        - Select the backend you want your program to run on via:
            - |_ `...piecewise_constant([durations], [values]).braket`:
                to run on Braket local emulator or QuEra hardware remotely
            - |_ `...piecewise_constant([durations], [values]).bloqade`:
                to run on the Bloqade local emulator
            - |_ `...piecewise_constant([durations], [values]).device`:
                to specify the backend via string
        - Choose to parallelize your atom geometry,
          duplicating it to fill the whole space:
            - |_ `...piecewise_constat([durations], [values]).parallelize(spacing)`
        - Start targeting another level coupling
            - |_ `...piecewise_constant([durations], [values]).rydberg`:
                to target the Rydberg level coupling
            - |_ `...piecewise_constant([durations], [values]).hyperfine`:
                to target the Hyperfine level coupling
        - Start targeting other fields within your current level coupling
          (previously selected as `rydberg` or `hyperfine`):
            - |_ `...piecewise_constant(durations, values).amplitude`:
                to target the real-valued Rabi Amplitude field
            - |_ `...piecewise_constant([durations], [values]).phase`:
                to target the real-valued Rabi Phase field
            - |_ `...piecewise_constant([durations], [values]).detuning`:
                to target the Detuning field
            - |_ `...piecewise_constant([durations], [values]).rabi`:
                to target the complex-valued Rabi field
        """
        return PiecewiseConstant(durations, values, self)

    @beartype
    def fn(self, fn: Callable, duration: ScalarType) -> "Fn":
        """
        Append or assign a custom function as a waveform.

        The function must have its first argument be that of time but
        can also have other arguments which are treated as variables.
        You can assign values to later in the program via `.assign` or `.batch_assign`.

        The function must also return a singular float value.

        If you specified a spatial modulation (e.g. `uniform`, `location`,`var`)
        previously without a waveform you will now have completed the construction
        of a "drive", one or a sum of drives creating a "field"
        (e.g. Real-valued Rabi Amplitude/Phase).

        If you have already specified a waveform previously you will now be appending
        this waveform to that previous waveform.

        Usage Examples:
        ```
        >>> prog = start.add_position((0,0)).rydberg.detuning.uniform
        # define our custom waveform. It must have one argument
        # be time followed by any other number of arguments that can
        # be assigned a value later in the program via `.assign` or `.batch_assign`
        >>> def custom_waveform_function(t, arg1, arg2):
                return arg1*t + arg2
        >>> prog = prog.fn(custom_waveform_function, duration = 0.5)
        # assign values
        >>> assigned_vars_prog = prog.assign(arg1 = 1.0, arg2 = 2.0)
        # or go for batching!
        >>> assigned_vars_batch_prog = prog.assign(arg1 = 1.0, arg2 = [1.0, 2.0, 3.0])
        ```

        - Your next steps include:
        - Continue building your waveform via:
            - |_ `...fn(f(t,...))
                .linear(start, stop, duration)`: to append another linear waveform
            - |_ `...fn(f(t,...))
                .constant(value, duration)`: to append a constant waveform
            - |_ `...fn(f(t,...))
                .piecewise_linear(durations, values)`:
                to append a piecewise linear waveform
            - |_ `...fn(f(t,...))
                .piecewise_constant(durations, values)`:
                to append a piecewise constant waveform
            - |_ `...fn(f(t,...))
                .poly([coefficients], duration)`: to append a polynomial waveform
            - |_ `...fn(f(t,...))
                .apply(waveform)`: to append a pre-defined waveform
            - |_ `...fn(f(t,...))
                .fn(f(t,...))`: to append a waveform defined by a python function
        - Slice a portion of the waveform to be used:
            - |_ `...fn(f(t,...)).slice(start, stop, duration)`
        - Save the ending value of your waveform to be reused elsewhere
            - |_ `...fn(f(t,...)).record("you_variable_here")`
        - Begin constructing another drive by starting a new spatial modulation
          (this drive will be summed to the one you just created):
            -|_ `...fn(f(t,...)).uniform`:
                To address all atoms in the field
            -|_ `...fn(f(t,...)).var(str)`:
                To address an atom at a specific location via index
            -|_ ...fn(f(t,...)).location(int)`
                - |_ To address an atom at a specific location via variable
                - |_ To address multiple atoms at specific locations by
                    specifying a single variable and then assigning it a
                    list of coordinates
        - Assign values to pre-existing variables via:
            - |_ `...fn(f(t,...))
                .assign(variable_name = value)`: to assign a single value to a variable
            - |_ `...fn(f(t,...))
                .batch_assign(variable_name = [value1, ...])`:
                to assign multiple values to a variable
            - |_ `...fn(f(t,...))
                .args(["previously_defined_var"])`:
                to defer assignment of a variable to execution time
        - Select the backend you want your program to run on via:
            - |_ `...fn(f(t,...)).braket`:
                to run on Braket local emulator or QuEra hardware remotely
            - |_ `...fn(f(t,...)).bloqade`:
                to run on the Bloqade local emulator
            - |_ `...fn(f(t,...)).device`:
                to specify the backend via string
        - Choose to parallelize your atom geometry,
          duplicating it to fill the whole space:
            - |_ `...fn(f(t,...)).parallelize(spacing)`
        - Start targeting another level coupling
            - |_ `...fn(f(t,...)).rydberg`:
                to target the Rydberg level coupling
            - |_ `...fn(f(t,...)).hyperfine`:
                to target the Hyperfine level coupling
        - Start targeting other fields within your current level coupling
          (previously selected as `rydberg` or `hyperfine`):
            - |_ `...fn(f(t,...)).amplitude`:
                to target the real-valued Rabi Amplitude field
            - |_ `...fn(f(t,...)).phase`:
                to target the real-valued Rabi Phase field
            - |_ `...fn(f(t,...)).detuning`:
                to target the Detuning field
            - |_ `...fn(f(t,...)).rabi`:
                to target the complex-valued Rabi field

        """
        return Fn(fn, duration, self)


# NOTE: waveform can refer previous pulse notes
#       or continue to specify pragma options
class Waveform(WaveformRoute, WaveformAttachable):
    pass


# mixin for slice and record
class Sliceable:
    @beartype
    def slice(
        self,
        start: Optional[ScalarType] = None,
        stop: Optional[ScalarType] = None,
    ) -> "Slice":
        """
        Indicate that you only want a portion of your waveform to be used in
        the program.

        If you specified a spatial modulation (e.g. `uniform`, `location`,`var`)
        previously without a waveform you will now have completed the construction
        of a "drive", one or a sum of drives creating a "field"
        (e.g. Real-valued Rabi Amplitude/Phase).

        If you have already specified a waveform previously you will now be appending
        this waveform to that previous waveform.


        Usage Example:
        ```
        # define a program with a waveform of interest
        >>> from bloqade import start
        >>> prog = start.add_position((0,0)).rydberg.rabi.amplitude.uniform
        >>> prog_with_wf = prog.piecewise_linear(durations=[0.3, 2.0, 0.3],
        values=[0.0, 2.0, 2.0, 0.0])
        # instead of using the full waveform we opt to only take the first 1 us
        >>> prog_with_slice = prog_with_wf.slice(0.0, 1.0)
        # you may use variables as well
        >>> prog_with_slice = prog_with_wf.slice("start", "end")
        ```

        - Your next steps include:
        - Continue building your waveform via:
            - |_ `...slice(start, stop).linear(start, stop, duration)`:
                to append another linear waveform
            - |_ `...slice(start, stop).constant(value, duration)`:
                to append a constant waveform
            - |_ `...slice(start, stop).piecewise_linear()`:
                to append a piecewise linear waveform
            - |_ `...slice(start, stop).piecewise_constant()`:
                to append a piecewise constant waveform
            - |_ `...slice(start, stop).poly([coefficients], duration)`:
                to append a polynomial waveform
            - |_ `...slice(start, stop).apply(wf:bloqade.ir.Waveform)`:
                to append a pre-defined waveform
            - |_ `...slilce(start, stop).fn(f(t,...))`:
                to append a waveform defined by a python function
        - Begin constructing another drive by starting a new spatial modulation
            (this drive will be summed to the one you just created):
            - |_ `...slice(start, stop).uniform`:
                To address all atoms in the field
            - |_ `...slice(start, stop).location(int)`:
                To address an atom at a specific location via index
            - |_ `...slice(start, stop).var(str)`
                - |_ To address an atom at a specific location via variable
                - |_ To address multiple atoms at specific locations by specifying
                    a single variable and then assigning it a list of coordinates
        - Assign values to pre-existing variables via:
            - |_ `...slice(start, stop).assign(variable_name = value)`:
                to assign a single value to a variable
            - |_ `...slice(start, stop)
                .batch_assign(variable_name = [value1, ...])`:
                to assign multiple values to a variable
            - |_ `...slice(start, stop).args(["previously_defined_var"])`:
                to defer assignment of a variable to execution time
        - Select the backend you want your program to run on via:
            - |_ `...slice(start, stop).braket`:
                to run on Braket local emulator or QuEra hardware remotely
            - |_ `...slice(start, stop).bloqade`:
                to run on the Bloqade local emulator
            - |_ `...slice(start, stop).device`:
                to specify the backend via string
        - Choose to parallelize your atom geometry,
          duplicating it to fill the whole space:
            - |_ `...slice(start, stop).parallelize(spacing)`
        - Start targeting another level coupling
            - |_ `...slice(start, stop).rydberg`:
                to target the Rydberg level coupling
            - |_ `...slice(start, stop).hyperfine`:
                to target the Hyperfine level coupling
        - Start targeting other fields within your current level coupling
          (previously selected as `rydberg` or `hyperfine`):
            - |_ `...slice(start, stop).amplitude`:
                to target the real-valued Rabi Amplitude field
            - |_ `...slice(start, stop).phase`:
                to target the real-valued Rabi Phase field
            - |_ `...slice(start, stop).detuning`:
                to target the Detuning field
            - |_ `...slice(start, stop).rabi`:
                to target the complex-valued Rabi field
        """
        return Slice(start, stop, self)


class Recordable:
    @beartype
    def record(self, name: str) -> "Record":
        """
        Copy or "record" the value at the end of the waveform into a variable
        so that it can be used in another place.

        A common design pattern is to couple this with `.slice()` considering
        you may not know exactly what the end value of a `.slice()` is,
        especially in parameter sweeps where it becomes cumbersome to handle.

        If you specified a spatial modulation (e.g. `uniform`, `location`,`var`)
        previously without a waveform you will now have completed the construction
        of a "drive", one or a sum of drives creating a "field"
        (e.g. Real-valued Rabi Amplitude/Phase).

        If you have already specified a waveform previously you will now be appending
        this waveform to that previous waveform.

        Usage Example:
        ```
        # define program of interest
        >>> from bloqade import start
        >>> prog = start.rydberg.rabi.amplitude.uniform
        >>> prog_with_wf = prog.piecewise_linear(durations=[0.3, 2.0, 0.3],
        values=[0.0, 2.0, 2.0, 0.0])
        # We now slice the piecewise_linear from above and record the
        # value at the end of that slice. We then use that value
        # to construct a new waveform that can be appended to the previous
        # one without introducing discontinuity (refer to the
        # "Quantum Scar Dynamics" tutorial for how this could be handy)
        >>> prog_with_record = prog_with_wf.slice(0.0, 1.0).record("end_of_wf")
        >>> record_applied_prog = prog_with_record.linear(start="end_of_wf"
        , stop=0.0, duration=0.3)
        ```

        - Your next steps include:
        - Continue building your waveform via:
            - |_ `...slice(start, stop).linear(start, stop, duration)`:
                to append another linear waveform
            - |_ `...slice(start, stop).constant(value, duration)`:
                to append a constant waveform
            - |_ `...slice(start, stop).piecewise_linear()`:
                to append a piecewise linear waveform
            - |_ `...slice(start, stop).piecewise_constant()`:
                to append a piecewise constant waveform
            - |_ `...slice(start, stop).poly([coefficients], duration)`:
                to append a polynomial waveform
            - |_ `...slice(start, stop).apply(wf:bloqade.ir.Waveform)`:
                to append a pre-defined waveform
            - |_ `...slilce(start, stop).fn(f(t,...))`:
                to append a waveform defined by a python function
        - Begin constructing another drive by starting a new spatial modulation
            (this drive will be summed to the one you just created):
            - |_ `...slice(start, stop).uniform`:
                To address all atoms in the field
            - |_ `...slice(start, stop).location(int)`:
                To address an atom at a specific location via index
            - |_ `...slice(start, stop).var(str)`
                - |_ To address an atom at a specific location via variable
                - |_ To address multiple atoms at specific locations by specifying
                    a single variable and then assigning it a list of coordinates
        - Assign values to pre-existing variables via:
            - |_ `...slice(start, stop).assign(variable_name = value)`:
                to assign a single value to a variable
            - |_ `...slice(start, stop)
                .batch_assign(variable_name = [value1, ...])`:
                to assign multiple values to a variable
            - |_ `...slice(start, stop).args(["previously_defined_var"])`:
                to defer assignment of a variable to execution time
        - Select the backend you want your program to run on via:
            - |_ `...slice(start, stop).braket`:
                to run on Braket local emulator or QuEra hardware remotely
            - |_ `...slice(start, stop).bloqade`:
                to run on the Bloqade local emulator
            - |_ `...slice(start, stop).device`:
                to specify the backend via string
        - Choose to parallelize your atom geometry,
          duplicating it to fill the whole space:
            - |_ `...slice(start, stop).parallelize(spacing)`
        - Start targeting another level coupling
            - |_ `...slice(start, stop).rydberg`:
                to target the Rydberg level coupling
            - |_ `...slice(start, stop).hyperfine`:
                to target the Hyperfine level coupling
        - Start targeting other fields within your current level coupling
          (previously selected as `rydberg` or `hyperfine`):
            - |_ `...slice(start, stop).amplitude`:
                to target the real-valued Rabi Amplitude field
            - |_ `...slice(start, stop).phase`:
                to target the real-valued Rabi Phase field
            - |_ `...slice(start, stop).detuning`:
                to target the Detuning field
            - |_ `...slice(start, stop).rabi`:
                to target the complex-valued Rabi field
        ```
        """
        return Record(name, self)


class WaveformPrimitive(Waveform, Sliceable, Recordable):
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


class Record(Waveform, Sliceable):  # record should not be sliceable
    __match_args__ = ("_name", "__parent__")

    def __init__(
        self,
        name: str,
        parent: Optional[Builder] = None,
    ) -> None:
        super().__init__(parent)
        self._name = ir.var(name)


class Sample(Sliceable, Recordable, WaveformRoute):
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
