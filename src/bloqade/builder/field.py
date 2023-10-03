from bloqade.builder.base import Builder
from bloqade.builder.typing import ScalarType
from beartype.typing import Union, List, Optional
import plum


class Field(Builder):
    @property
    def uniform(self):
        """
        Address all atoms as part of defining the spatial modulation component
        of a drive.

        Next steps to build your program include choosing the waveform that
        will be summed with the spatial modulation to create a drive.

        The drive by itself, or the sum of subsequent drives (created by just
        chaining the construction of drives) will become the field
        (e.g. Detuning Field, Real-Valued Rabi Amplitude/Rabi Phase Field, etc.).

        - You can now do:
            - `...uniform.linear(start, stop, duration)` : to apply a linear waveform
            - `...uniform.constant(value, duration)` : to apply a constant waveform
            - `...uniform.poly([coefficients], duration)` : to apply a
                polynomial waveform
            - `...uniform.apply(wf:bloqade.ir.Waveform)`: to apply a
            pre-defined waveform
            - `...uniform.piecewise_linear([durations], [values])`:  to apply
            a piecewise linear waveform
            - `...uniform.piecewise_constant([durations], [values])`: to apply
            a piecewise constant waveform
            - `...uniform.fn(f(t,...))`: to apply a function as a waveform

        """
        from bloqade.builder.spatial import Uniform

        return Uniform(self)

    @plum.dispatch
    def _location(self, label: int, scale: Optional[ScalarType] = None):  # noqa: F811
        from bloqade.builder.spatial import Location

        if scale is None:
            scale = 1

        return Location([label], [scale], self)

    @plum.dispatch
    def _location(
        self, labels: List[int], scales: Optional[List[ScalarType]] = None
    ):  # noqa: F811
        from bloqade.builder.spatial import Location

        if scales is None:
            scales = [1] * len(labels)

        return Location(labels, scales, self)

    def location(
        self,
        labels: Union[List[int], int],
        scales: Union[List[ScalarType], ScalarType, None] = None,
    ):
        """Address a single atom (or multiple) atoms.

        Address a single atom (or multiple) as part of defining the spatial
        modulation component of a drive. You can specify the atoms to target
        as a list of labels and a list of scales. The scales are used to
        multiply the waveform that is applied to the atom. You can also specify
        a single label and scale to target a single atom.

        Next steps to build your program include choosing the waveform that
        will be summed with the spatial modulation to create a drive.

        The drive by itself, or the sum of subsequent drives (created by just
        chaining the construction of drives) will become the field.
        (e.g. Detuning Field, Real-Valued Rabi Amplitude/Rabi Phase Field, etc.)

        ### Usage Example:
        ```
        >>> prog = start.add_position([(0,0),(1,4),(2,8)]).rydberg.rabi
        # to target a single atom with a waveform
        >>> one_location_prog = prog.location(0)
        # to target a single atom with a scale
        >>> one_location_prog = prog.location(0, 0.5)
        # to target multiple atoms with same waveform
        >>> multi_location_prog = prog.location([0, 2])
        # to target multiple atoms with different scales
        >>> multi_location_prog = prog.location([0, 2], [0.5, "scale"])
        ```

        - You can now do:
            - `...location(...).linear(start, stop, duration)` : to apply
                a linear waveform
            - `...location(...).constant(value, duration)` : to apply
                a constant waveform
            - `...location(...).poly([coefficients], duration)` : to apply
                a polynomial waveform
            - `...location(...).apply(wf:bloqade.ir.Waveform)`: to apply
                a pre-defined waveform
            - `...location(...).piecewise_linear([durations], [values])`:  to apply
                a piecewise linear waveform
            - `...location(...).piecewise_constant([durations], [values])`: to apply
                a piecewise constant waveform
            - `...location(...).fn(f(t,..))`: to apply a function as a waveform

        """
        return self._location(labels, scales)

    def scale(self, name_or_list: Union[str, List[ScalarType]]):
        """
        Address all the atoms scaling each atom with an element of the list
        or define a variable name for the scale list to be assigned later by
        defining a `name` and using `assign` or `batch_assign` later.

        Next steps to build your program include choosing the waveform that
        will be summed with the spatial modulation to create a drive.

        The drive by itself, or the sum of subsequent drives (created by just
        chaining the construction of drives) will become the field
        (e.g. Detuning Field, Real-Valued Rabi Amplitude/Rabi Phase Field, etc.)

        ### Usage Example:
        ```
        >>> prog = start.add_position([(0,0),(1,4),(2,8)]).rydberg.rabi

        # assign a literal list of values to scale each atom
        >>> one_location_prog = prog.scale([0.1, 0.2, 0.3])
        # assign a variable name to be assigned later
        >>> one_location_prog = prog.scale("a")
        # "a" can be assigned in the END of the program during variable assignment
        # using a list of values, indicating the scaling for each atom
        >>> single_assignment = ...assign(a = [0.1, 0.2, 0.3])
        # a list of lists, indicating a set of atoms should be targeted
        # for each task in a batch.
        >>> batch_assignment = ...batch_assign(a = [list_1, list_2, list_3,...])

        ```

        - You can now do:
            - `...scale(...).linear(start, stop, duration)` : to apply
                a linear waveform
            - `...scale(...).constant(value, duration)` : to apply
                a constant waveform
            - `...scale(...).poly([coefficients], duration)` : to apply
                a polynomial waveform
            - `...scale(...).apply(wf:bloqade.ir.Waveform)`: to apply
                a pre-defined waveform
            - `...scale(...).piecewise_linear(durations, values)`:  to
                apply a piecewise linear waveform
            - `...scale(...).piecewise_constant(durations, values)`: to
                apply a piecewise constant waveform
            - `...scale(...).fn(f(t,..))`: to apply a function as a waveform

        """
        from bloqade.builder.spatial import Var

        return Var(name_or_list, self)


class Detuning(Field):
    """
    This node represent detuning field of a
    specified level coupling (rydberg or hyperfine) type.


    Examples:

        - To specify detuning of rydberg coupling:

        >>> node = bloqade.start.rydberg.detuning
        >>> type(node)
        <class 'bloqade.builder.field.Detuning'>

        - To specify detuning of hyperfine coupling:

        >>> node = bloqade.start.hyperfine.detuning
        >>> type(node)
        <class 'bloqade.builder.field.Detuning'>

    Note:
        This node is a SpatialModulation node.
        See [`SpatialModulation`][bloqade.builder.field.SpatialModulation]
        for additional options.

    """

    def __bloqade_ir__(self):
        from bloqade.ir.control.pulse import detuning

        return detuning


# this is just an eye candy, thus
# it's not the actual Field object
# one can skip this node when doing
# compilation
class Rabi(Builder):
    """
    This node represent rabi field of a
    specified level coupling (rydberg or hyperfine) type.

    Examples:

        - To specify rabi of rydberg coupling:

        >>> node = bloqade.start.rydberg.rabi
        <class 'bloqade.builder.field.Rabi'>

        - To specify rabi of hyperfine coupling:

        >>> node = bloqade.start.hyperfine.rabi
        >>> type(node)
        <class 'bloqade.builder.field.Rabi'>


    """

    @property
    def amplitude(self) -> "RabiAmplitude":
        """
        Specify the real-valued Rabi Amplitude field.

        Next steps to build your program focus on specifying a spatial
        modulation.

        The spatial modulation, when coupled with a waveform, completes the
        specification of a "Drive". One or more drives can be summed together
        automatically to create a field such as the Rabi Amplitude here.

        - You can now
            - `...amplitude.uniform`: address all atoms in the field
            - `...amplitude.location(int)`: address a specific atom by its
                index
            - `...amplitude.var(str)`: Address a single atom
                (or multiple via assigning a list of values)

        """
        return RabiAmplitude(self)

    @property
    def phase(self) -> "RabiPhase":
        """
        Specify the real-valued Rabi Phase field.

        Next steps to build your program focus on specifying a spatial
        modulation.

        The spatial modulation, when coupled with a waveform, completes the
        specification of a "Drive". One or more drives can be summed together
        automatically to create a field such as the Rabi Phase here.

        - You can now
            - `...amplitude.uniform`: address all atoms in the field
            - `...amplitude.location(int)`: address a specific atom by its
                index
            - `...amplitude.var(str)`: Address a single atom
                (or multiple via assigning a list of values)

        """
        return RabiPhase(self)


class RabiAmplitude(Field):
    """
    This node represent amplitude of a rabi field.

    Examples:

        - To specify rabi amplitude of rydberg coupling:

        >>> node = bloqade.start.rydberg.rabi.amplitude
        >>> type(node)
        <class 'bloqade.builder.field.Amplitude'>

        - To specify rabi amplitude of hyperfine coupling:

        >>> node = bloqade.start.hyperfine.rabi.amplitude
        >>> type(node)
        <class 'bloqade.builder.field.Amplitude'>

    Note:
        This node is a SpatialModulation node.
        See [`SpatialModulation`][bloqade.builder.field.SpatialModulation]
        for additional options.

    """

    def __bloqade_ir__(self):
        from bloqade.ir.control.pulse import rabi

        return rabi.amplitude


class RabiPhase(Field):
    """
    This node represent phase of a rabi field.

    Examples:

        - To specify rabi phase of rydberg coupling:

        >>> node = bloqade.start.rydberg.rabi.phase
        >>> type(node)
        <class 'bloqade.builder.field.Phase'>

        - To specify rabi phase of hyperfine coupling:

        >>> node = bloqade.start.hyperfine.rabi.phase
        >>> type(node)
        <class 'bloqade.builder.field.Phase'>

    Note:
        This node is a SpatialModulation node.
        See [`SpatialModulation`][bloqade.builder.field.SpatialModulation]
        for additional options.
    """

    def __bloqade_ir__(self):
        from bloqade.ir.control.pulse import rabi

        return rabi.phase
