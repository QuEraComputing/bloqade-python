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

        ### Usage Example:
        ```
        >>> prog = start.add_position((0,0)).rydberg.detuning.uniform
        # apply a linear waveform that goes from 0 to 1 radians/us in 0.5 us
        >>> prog.linear(start=0,stop=1,duration=0.5)
        ```

        - Your next steps include:
        - Continue building your waveform via:
            - `...linear(start, stop, duration).linear(start, stop, duration)`:
                to append another linear waveform
            - `...linear(start, stop, duration).constant(value, duration)`:
                to append a constant waveform
            - `...linear(start, stop, duration)
                .piecewise_linear([durations], [values])`:
                to append a piecewise linear waveform
            - `...linear(start, stop, duration)
                .piecewise_constant([durations], [values])`:
                to append a piecewise constant waveform
            - `...linear(start, stop, duration).poly([coefficients], duration)`:
                to append a polynomial waveform
            - `...linear(start, stop, duration).apply(wf:bloqade.ir.Waveform)`:
                to append a pre-defined waveform
            - `...linear(start, stop, duration).fn(f(t,...))`:
                to append a waveform defined by a python function
        - Slice a portion of the waveform to be used:
            - `...linear(start, stop, duration).slice(start, stop, duration)`
        - Save the ending value of your waveform to be reused elsewhere
            - `...linear(start, stop, duration).record("you_variable_here")`
        - Begin constructing another drive by starting a new spatial modulation
            (this drive will be summed to the one you just created):
            - `...linear(start, stop, duration).uniform`:
                To address all atoms in the field
            - `...linear(start, stop, duration).location(int)`:
                To address an atom at a specific location via index
            - `...linear(start, stop, duration).var(str)`
                - To address an atom at a specific location via variable
                - To address multiple atoms at specific locations by specifying
                    a single variable and then assigning it a list of coordinates
        - Assign values to pre-existing variables via:
            - `...linear(start, stop, duration).assign(variable_name = value)`:
                to assign a single value to a variable
            - `...linear(start, stop, duration)
                .batch_assign(variable_name = [value1, ...])`:
                to assign multiple values to a variable
            - `...linear(start, stop, duration).args(["previously_defined_var"])`:
                to defer assignment of a variable to execution time
        - Select the backend you want your program to run on via:
            - `...linear(start, stop, duration).braket`:
                to run on Braket local emulator or QuEra hardware remotely
            - `...linear(start, stop, duration).bloqade`:
                to run on the Bloqade local emulator
            - `...linear(start, stop, duration).device`:
                to specify the backend via string
        - Choose to parallelize your atom geometry,
          duplicating it to fill the whole space:
            - `...linear(start, stop, duration).parallelize(spacing)`
        - Start targeting another level coupling
            - `...linear(start, stop, duration).rydberg`:
                to target the Rydberg level coupling
            - `...linear(start, stop, duration).hyperfine`:
                to target the Hyperfine level coupling
        - Start targeting other fields within your current level coupling
          (previously selected as `rydberg` or `hyperfine`):
            - `...linear(start, stop, duration).amplitude`:
                to target the real-valued Rabi Amplitude field
            - `...linear(start, stop, duration).phase`:
                to target the real-valued Rabi Phase field
            - `...linear(start, stop, duration).detuning`:
                to target the Detuning field
            - `...linear(start, stop, duration).rabi`:
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

        ### Usage Example:
        ```
        >>> prog = start.add_position((0,0)).rydberg.detuning.uniform
        # apply a constant waveform of 1.9 radians/us for 0.5 us
        >>> prog.constant(value=1.9,duration=0.5)
        ```

        - Your next steps include:
        - Continue building your waveform via:
            - `...constant(value, duration).linear(start, stop, duration)`:
                to append another linear waveform
            - `...constant(value, duration).constant(value, duration)`:
                to append a constant waveform
            - `...constant(value, duration)
                .piecewise_linear([durations], [values])`:
                to append a piecewise linear waveform
            - `...constant(value, duration)
                .piecewise_constant([durations], [values])`:
                to append a piecewise constant waveform
            - `...constant(value, duration).poly([coefficients], duration)`:
                to append a polynomial waveform
            - `...constant(value, duration).apply(wf:bloqade.ir.Waveform)`:
                to append a pre-defined waveform
            - `...constant(value, duration).fn(f(t,...))`:
                to append a waveform defined by a python function
        - Slice a portion of the waveform to be used:
            - `...constant(value, duration).slice(start, stop, duration)`
        - Save the ending value of your waveform to be reused elsewhere
            - `...constant(value, duration).record("you_variable_here")`
        - Begin constructing another drive by starting a new spatial modulation
            (this drive will be summed to the one you just created):
            - `...constant(value, duration).uniform`:
                To address all atoms in the field
            - `...constant(value, duration).var`:
                To address an atom at a specific location via index
            - `...constant(value, duration).location(int)`
                - To address an atom at a specific location via variable
                - To address multiple atoms at specific locations by specifying
                    a single variable and then assigning it a list of coordinates
        - Assign values to pre-existing variables via:
            - `...constant(value, duration).assign(variable_name = value)`:
                to assign a single value to a variable
            - `...constant(value, duration)
                .batch_assign(variable_name = [value1, ...])`:
                to assign multiple values to a variable
            - `...constant(value, duration).args(["previously_defined_var"])`:
                to defer assignment of a variable to execution time
        - Select the backend you want your program to run on via:
            - `...constant(value, duration).braket`:
                to run on Braket local emulator or QuEra hardware remotely
            - `...constant(value, duration).bloqade`:
                to run on the Bloqade local emulator
            - `...constant(value, duration).device`:
                to specify the backend via string
        - Choose to parallelize your atom geometry,
          duplicating it to fill the whole space:
            - `...constant(start, stop, duration).parallelize(spacing)`
        - Start targeting another level coupling
            - `...constant(value, duration).rydberg`:
                to target the Rydberg level coupling
            - `...constant(value, duration).hyperfine`:
                to target the Hyperfine level coupling
        - Start targeting other fields within your current
          level coupling (previously selected as `rydberg` or `hyperfine`):
            - `...constant(value, duration).amplitude`:
                to target the real-valued Rabi Amplitude field
            - `...constant(value, duration).phase`:
                to target the real-valued Rabi Phase field
            - `...constant(value, duration).detuning`:
                to target the Detuning field
            - `...constant(value, duration).rabi`:
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

        ### Usage Example:
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
            - `...poly([coeffs], duration).linear(start, stop, duration)`:
                to append another linear waveform
            - `...poly([coeffs], duration).constant(value, duration)`:
                to append a constant waveform
            - `...poly([coeffs], duration)
                .piecewise_linear([durations], [values])`:
                to append a piecewise linear waveform
            - `...poly([coeffs], duration)
                .piecewise_constant([durations],[values])`:
                to append a piecewise constant waveform
            - `...poly([coeffs], duration).poly([coefficients], duration)`:
                to append a polynomial waveform
            - `...poly([coeffs], duration).apply(waveform)`:
                to append a pre-defined waveform
            - `...poly([coeffs], duration).fn(f(t,...))`:
                to append a waveform defined by a python function
        - Slice a portion of the waveform to be used:
            - `...poly([coeffs], duration).slice(start, stop, duration)`
        - Save the ending value of your waveform to be reused elsewhere
            - `...poly([coeffs], duration).record("you_variable_here")`
        - Begin constructing another drive by starting a new spatial modulation
          (this drive will be summed to the one you just created):
            - `...poly([coeffs], duration).uniform`:
                To address all atoms in the field
            - `...poly([coeffs], duration).location(int)`:
                To address an atom at a specific location via index
            - `...poly([coeffs], duration).var(str)`
                - To address an atom at a specific location via variable
                - To address multiple atoms at specific locations by
                    specifying a single variable and then assigning
                    it a list of coordinates
        - Assign values to pre-existing variables via:
            - `...poly([coeffs], duration).assign(variable_name = value)`:
                to assign a single value to a variable
            - `...poly([coeffs], duration)
                .batch_assign(variable_name = [value1, ...])`:
                to assign multiple values to a variable
            - `...poly([coeffs], duration).args(["previously_defined_var"])`:
                to defer assignment of a variable to execution time
        - Select the backend you want your program to run on via:
            - `...poly([coeffs], duration).braket`:
                to run on Braket local emulator or QuEra hardware remotely
            - `...poly([coeffs], duration).bloqade`:
                to run on the Bloqade local emulator
            - `...poly([coeffs], duration).device`:
                to specify the backend via string
        - Choose to parallelize your atom geometry,
          duplicating it to fill the whole space:
            - `...poly([coeffs], duration).parallelize(spacing)`
        - Start targeting another level coupling
            - `...poly([coeffs], duration).rydberg`:
                to target the Rydberg level coupling
            - `...poly([coeffs], duration).hyperfine`:
                to target the Hyperfine level coupling
        - Start targeting other fields within your current level
          coupling (previously selected as `rydberg` or `hyperfine`):
            - `...poly([coeffs], duration).amplitude`:
                to target the real-valued Rabi Amplitude field
            - `...poly([coeffs], duration).phase`:
                to target the real-valued Rabi Phase field
            - `...poly([coeffs], duration).detuning`:
                to target the Detuning field
            - `...poly([coeffs], duration).rabi`:
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

        ### Usage Example:
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
            - `...apply(waveform).linear(start, stop, duration)`:
                to append another linear waveform
            - `...apply(waveform).constant(value, duration)`:
                to append a constant waveform
            - `...apply(waveform).piecewise_linear([durations], [values])`:
                to append a piecewise linear waveform
            - `...apply(waveform).piecewise_constant([durations], [values])`:
                to append a piecewise constant waveform
            - `...apply(waveform).poly([coefficients], duration)`:
                to append a polynomial waveform
            - `...apply(waveform).apply(waveform)`:
                to append a pre-defined waveform
            - `...apply(waveform).fn(f(t,...))`:
                to append a waveform defined by a python function
        - Slice a portion of the waveform to be used:
            - `...apply(waveform).slice(start, stop, duration)`
        - Save the ending value of your waveform to be reused elsewhere
            - `...apply(waveform).record("you_variable_here")`
        - Begin constructing another drive by starting a new spatial modulation
          (this drive will be summed to the one you just created):
            - `...apply(waveform).uniform`: To address all atoms in the field
            - `...apply(waveform).location(int)`:
                To address an atom at a specific location via index
            - `...apply(waveform).var(str)`
                - To address an atom at a specific location via variable
                - To address multiple atoms at specific locations by specifying a
                    single variable and then assigning it a list of coordinates
        - Assign values to pre-existing variables via:
            - `...apply(waveform).assign(variable_name = value)`:
                to assign a single value to a variable
            - `...apply(waveform).batch_assign(variable_name = [value1, ...])`:
                to assign multiple values to a variable
            - `...apply(waveform).args(["previously_defined_var"])`:
                to defer assignment of a variable to execution time
        - Select the backend you want your program to run on via:
            - `...apply(waveform).braket`:
                to run on Braket local emulator or QuEra hardware remotely
            - `...apply(waveform).bloqade`:
                to run on the Bloqade local emulator
            - `...apply(waveform).device`:
                to specify the backend via string
        - Choose to parallelize your atom geometry,
          duplicating it to fill the whole space:
            - `...apply(waveform).parallelize(spacing)`
        - Start targeting another level coupling
            - `...apply(waveform).rydberg`: to target the Rydberg level coupling
            - `...apply(waveform).hyperfine`: to target the Hyperfine level coupling
        - Start targeting other fields within your current level coupling
          (previously selected as `rydberg` or `hyperfine`):
            - `...apply(waveform).amplitude`:
                to target the real-valued Rabi Amplitude field
            - `...apply(waveform).phase`:
                to target the real-valued Rabi Phase field
            - `...apply(waveform).detuning`:
                to target the Detuning field
            - `...apply(waveform).rabi`:
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

        ### Usage Example:
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
            - `...piecewise_linear([durations], [values])
                .linear(start, stop, duration)`:
                to append another linear waveform
            - `...piecewise_linear([durations], [values]).constant(value, duration)`:
                to append a constant waveform
            - `...piecewise_linear([durations], [values])
                .piecewise_linear(durations, values)`:
                to append a piecewise linear waveform
            - `...piecewise_linear([durations], [values])
                .piecewise_constant([durations], [values])`:
                to append a piecewise constant waveform
            - `...piecewise_linear([durations], [values])
                .poly([coefficients], duration)`: to append a polynomial waveform
            - `...piecewise_linear([durations], [values]).apply(waveform)`:
                to append a pre-defined waveform
            - `...piecewise_linear([durations], [values]).fn(f(t,...))`:
                to append a waveform defined by a python function
        - Slice a portion of the waveform to be used:
            - `...piecewise_linear([durations], [values])
                .slice(start, stop, duration)`
        - Save the ending value of your waveform to be reused elsewhere
            - `...piecewise_linear([durations], [values])
                .record("you_variable_here")`
        - Begin constructing another drive by starting a new spatial modulation
          (this drive will be summed to the one you just created):
            - `...piecewise_linear([durations], [values]).uniform`:
                To address all atoms in the field
            - `...piecewise_linear([durations], [values]).var`:
                To address an atom at a specific location via index
            - `...piecewise_linear([durations], [values]).location(int)`
                - To address an atom at a specific location via variable
                - To address multiple atoms at specific locations by
                    specifying a single variable and then assigning it a
                    list of coordinates
        - Assign values to pre-existing variables via:
            - `...piecewise_linear([durations], [values])
                .assign(variable_name = value)`:
                to assign a single value to a variable
            - `...piecewise_linear([durations], [values])
                .batch_assign(variable_name = [value1, ...])`:
                to assign multiple values to a variable
            - `...piecewise_linear([durations], [values])
                .args(["previously_defined_var"])`:
                to defer assignment of a variable to execution time
        - Select the backend you want your program to run on via:
            - `...piecewise_linear([durations], [values]).braket`:
                to run on Braket local emulator or QuEra hardware remotely
            - `...piecewise_linear([durations], [values]).bloqade`:
                to run on the Bloqade local emulator
            - `...piecewise_linear([durations], [values]).device`:
                to specify the backend via string
        - Choose to parallelize your atom geometry,
          duplicating it to fill the whole space:
            - `...piecewise_linear([durations], [values]).parallelize(spacing)`
        - Start targeting another level coupling
            - `...piecewise_linear([durations], [values]).rydberg`:
                to target the Rydberg level coupling
            - `...piecewise_linear([durations], [values]).hyperfine`:
                to target the Hyperfine level coupling
        - Start targeting other fields within your current level coupling
          (previously selected as `rydberg` or `hyperfine`):
            - `...piecewise_linear([durations], [values]).amplitude`:
                to target the real-valued Rabi Amplitude field
            - `...piecewise_linear([durations], [values]).phase`:
                to target the real-valued Rabi Phase field
            - `...piecewise_linear([durations], [values]).detuning`:
                to target the Detuning field
            - `....rabi`: to target the complex-valued Rabi field
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

        ### Usage Example:
        ```
        >>> prog = start.add_position((0,0)).rydberg.rabi.phase.uniform
        # create a staircase, we hold 0.0 rad/us for 1.0 us, then
        # to 1.0 rad/us for 0.5 us before stopping at 0.8 rad/us for 0.9 us.
        >>> prog.piecewise_linear(durations=[0.3, 2.0, 0.3], values=[1.0, 0.5, 0.9])
        ```

        - Your next steps including:
        - Continue building your waveform via:
            - `...piecewise_constant([durations], [values])
                .linear(start, stop, duration)`: to append another linear waveform
            - `...piecewise_constant([durations], [values])
                .constant(value, duration)`: to append a constant waveform
            - `...piecewise_constant([durations], [values])
                .piecewise_linear([durations], [values])`:
                to append a piecewise linear waveform
            - `...piecewise_constant([durations], [values])
                .piecewise_constant([durations], [values])`:
                to append a piecewise constant waveform
            - `...piecewise_constant([durations], [values])
                .poly([coefficients], duration)`: to append a polynomial waveform
            - `...piecewise_constant([durations], [values])
                .apply(waveform)`: to append a pre-defined waveform
            - `...piecewise_constant([durations], [values]).fn(f(t,...))`:
                to append a waveform defined by a python function
        - Slice a portion of the waveform to be used:
            - `...piecewise_constant([durations], [values])
                .slice(start, stop, duration)`
        - Save the ending value of your waveform to be reused elsewhere
            - `...piecewise_constant([durations], [values])
                .record("you_variable_here")`
        - Begin constructing another drive by starting a new spatial modulation
          (this drive will be summed to the one you just created):
            - `...piecewise_constant([durations], [values]).uniform`:
                To address all atoms in the field
            - `...piecewise_constant([durations], [values]).location(int)`:
                To address an atom at a specific location via index
            - `...piecewise_constant([durations], [values]).var(str)`
                - To address an atom at a specific location via variable
                - To address multiple atoms at specific locations by
                    specifying a single variable and then assigning it a
                    list of coordinates
        - Assign values to pre-existing variables via:
            - `...piecewise_constant([durations], [values])
                .assign(variable_name = value)`: to assign a single value to a variable
            - `...piecewise_constant([durations], [values])
                .batch_assign(variable_name = [value1, ...])`:
                to assign multiple values to a variable
            - `...piecewise_constant([durations], [values])
                .args(["previously_defined_var"])`: to defer assignment
                of a variable to execution time
        - Select the backend you want your program to run on via:
            - `...piecewise_constant([durations], [values]).braket`:
                to run on Braket local emulator or QuEra hardware remotely
            - `...piecewise_constant([durations], [values]).bloqade`:
                to run on the Bloqade local emulator
            - `...piecewise_constant([durations], [values]).device`:
                to specify the backend via string
        - Choose to parallelize your atom geometry,
          duplicating it to fill the whole space:
            - `...piecewise_constat([durations], [values]).parallelize(spacing)`
        - Start targeting another level coupling
            - `...piecewise_constant([durations], [values]).rydberg`:
                to target the Rydberg level coupling
            - `...piecewise_constant([durations], [values]).hyperfine`:
                to target the Hyperfine level coupling
        - Start targeting other fields within your current level coupling
          (previously selected as `rydberg` or `hyperfine`):
            - `...piecewise_constant(durations, values).amplitude`:
                to target the real-valued Rabi Amplitude field
            - `...piecewise_constant([durations], [values]).phase`:
                to target the real-valued Rabi Phase field
            - `...piecewise_constant([durations], [values]).detuning`:
                to target the Detuning field
            - `...piecewise_constant([durations], [values]).rabi`:
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

        ### ### Usage Examples:
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
            - `...fn(f(t,...))
                .linear(start, stop, duration)`: to append another linear waveform
            - `...fn(f(t,...))
                .constant(value, duration)`: to append a constant waveform
            - `...fn(f(t,...))
                .piecewise_linear(durations, values)`:
                to append a piecewise linear waveform
            - `...fn(f(t,...))
                .piecewise_constant(durations, values)`:
                to append a piecewise constant waveform
            - `...fn(f(t,...))
                .poly([coefficients], duration)`: to append a polynomial waveform
            - `...fn(f(t,...))
                .apply(waveform)`: to append a pre-defined waveform
            - `...fn(f(t,...))
                .fn(f(t,...))`: to append a waveform defined by a python function
        - Slice a portion of the waveform to be used:
            - `...fn(f(t,...)).slice(start, stop, duration)`
        - Save the ending value of your waveform to be reused elsewhere
            - `...fn(f(t,...)).record("you_variable_here")`
        - Begin constructing another drive by starting a new spatial modulation
          (this drive will be summed to the one you just created):
            - `...fn(f(t,...)).uniform`:
                To address all atoms in the field
            - `...fn(f(t,...)).var(str)`:
                To address an atom at a specific location via index
            - ...fn(f(t,...)).location(int)`
                - To address an atom at a specific location via variable
                - To address multiple atoms at specific locations by
                    specifying a single variable and then assigning it a
                    list of coordinates
        - Assign values to pre-existing variables via:
            - `...fn(f(t,...))
                .assign(variable_name = value)`: to assign a single value to a variable
            - `...fn(f(t,...))
                .batch_assign(variable_name = [value1, ...])`:
                to assign multiple values to a variable
            - `...fn(f(t,...))
                .args(["previously_defined_var"])`:
                to defer assignment of a variable to execution time
        - Select the backend you want your program to run on via:
            - `...fn(f(t,...)).braket`:
                to run on Braket local emulator or QuEra hardware remotely
            - `...fn(f(t,...)).bloqade`:
                to run on the Bloqade local emulator
            - `...fn(f(t,...)).device`:
                to specify the backend via string
        - Choose to parallelize your atom geometry,
          duplicating it to fill the whole space:
            - `...fn(f(t,...)).parallelize(spacing)`
        - Start targeting another level coupling
            - `...fn(f(t,...)).rydberg`:
                to target the Rydberg level coupling
            - `...fn(f(t,...)).hyperfine`:
                to target the Hyperfine level coupling
        - Start targeting other fields within your current level coupling
          (previously selected as `rydberg` or `hyperfine`):
            - `...fn(f(t,...)).amplitude`:
                to target the real-valued Rabi Amplitude field
            - `...fn(f(t,...)).phase`:
                to target the real-valued Rabi Phase field
            - `...fn(f(t,...)).detuning`:
                to target the Detuning field
            - `...fn(f(t,...)).rabi`:
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


        ### Usage Example:
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
            - `...slice(start, stop).linear(start, stop, duration)`:
                to append another linear waveform
            - `...slice(start, stop).constant(value, duration)`:
                to append a constant waveform
            - `...slice(start, stop).piecewise_linear()`:
                to append a piecewise linear waveform
            - `...slice(start, stop).piecewise_constant()`:
                to append a piecewise constant waveform
            - `...slice(start, stop).poly([coefficients], duration)`:
                to append a polynomial waveform
            - `...slice(start, stop).apply(wf:bloqade.ir.Waveform)`:
                to append a pre-defined waveform
            - `...slilce(start, stop).fn(f(t,...))`:
                to append a waveform defined by a python function
        - Begin constructing another drive by starting a new spatial modulation
            (this drive will be summed to the one you just created):
            - `...slice(start, stop).uniform`:
                To address all atoms in the field
            - `...slice(start, stop).location(int)`:
                To address an atom at a specific location via index
            - `...slice(start, stop).var(str)`
                - To address an atom at a specific location via variable
                - To address multiple atoms at specific locations by specifying
                    a single variable and then assigning it a list of coordinates
        - Assign values to pre-existing variables via:
            - `...slice(start, stop).assign(variable_name = value)`:
                to assign a single value to a variable
            - `...slice(start, stop)
                .batch_assign(variable_name = [value1, ...])`:
                to assign multiple values to a variable
            - `...slice(start, stop).args(["previously_defined_var"])`:
                to defer assignment of a variable to execution time
        - Select the backend you want your program to run on via:
            - `...slice(start, stop).braket`:
                to run on Braket local emulator or QuEra hardware remotely
            - `...slice(start, stop).bloqade`:
                to run on the Bloqade local emulator
            - `...slice(start, stop).device`:
                to specify the backend via string
        - Choose to parallelize your atom geometry,
          duplicating it to fill the whole space:
            - `...slice(start, stop).parallelize(spacing)`
        - Start targeting another level coupling
            - `...slice(start, stop).rydberg`:
                to target the Rydberg level coupling
            - `...slice(start, stop).hyperfine`:
                to target the Hyperfine level coupling
        - Start targeting other fields within your current level coupling
          (previously selected as `rydberg` or `hyperfine`):
            - `...slice(start, stop).amplitude`:
                to target the real-valued Rabi Amplitude field
            - `...slice(start, stop).phase`:
                to target the real-valued Rabi Phase field
            - `...slice(start, stop).detuning`:
                to target the Detuning field
            - `...slice(start, stop).rabi`:
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

        ### Usage Example:
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
            - `...slice(start, stop).linear(start, stop, duration)`:
                to append another linear waveform
            - `...slice(start, stop).constant(value, duration)`:
                to append a constant waveform
            - `...slice(start, stop).piecewise_linear()`:
                to append a piecewise linear waveform
            - `...slice(start, stop).piecewise_constant()`:
                to append a piecewise constant waveform
            - `...slice(start, stop).poly([coefficients], duration)`:
                to append a polynomial waveform
            - `...slice(start, stop).apply(wf:bloqade.ir.Waveform)`:
                to append a pre-defined waveform
            - `...slilce(start, stop).fn(f(t,...))`:
                to append a waveform defined by a python function
        - Begin constructing another drive by starting a new spatial modulation
            (this drive will be summed to the one you just created):
            - `...slice(start, stop).uniform`:
                To address all atoms in the field
            - `...slice(start, stop).location(int)`:
                To address an atom at a specific location via index
            - `...slice(start, stop).var(str)`
                - To address an atom at a specific location via variable
                - To address multiple atoms at specific locations by specifying
                    a single variable and then assigning it a list of coordinates
        - Assign values to pre-existing variables via:
            - `...slice(start, stop).assign(variable_name = value)`:
                to assign a single value to a variable
            - `...slice(start, stop)
                .batch_assign(variable_name = [value1, ...])`:
                to assign multiple values to a variable
            - `...slice(start, stop).args(["previously_defined_var"])`:
                to defer assignment of a variable to execution time
        - Select the backend you want your program to run on via:
            - `...slice(start, stop).braket`:
                to run on Braket local emulator or QuEra hardware remotely
            - `...slice(start, stop).bloqade`:
                to run on the Bloqade local emulator
            - `...slice(start, stop).device`:
                to specify the backend via string
        - Choose to parallelize your atom geometry,
          duplicating it to fill the whole space:
            - `...slice(start, stop).parallelize(spacing)`
        - Start targeting another level coupling
            - `...slice(start, stop).rydberg`:
                to target the Rydberg level coupling
            - `...slice(start, stop).hyperfine`:
                to target the Hyperfine level coupling
        - Start targeting other fields within your current level coupling
          (previously selected as `rydberg` or `hyperfine`):
            - `...slice(start, stop).amplitude`:
                to target the real-valued Rabi Amplitude field
            - `...slice(start, stop).phase`:
                to target the real-valued Rabi Phase field
            - `...slice(start, stop).detuning`:
                to target the Detuning field
            - `...slice(start, stop).rabi`:
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
        return ir.PythonFn.create(self._fn, self._duration)


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
