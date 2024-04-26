from bloqade.builder.base import Builder
from bloqade.builder.typing import ScalarType
from beartype.typing import Union, List, Optional, TYPE_CHECKING
import plum

if TYPE_CHECKING:
    from bloqade.builder.spatial import Uniform, Location, Scale


class Field(Builder):
    @property
    def uniform(self) -> "Uniform":
        """
        Address all atoms as part of defining the spatial modulation component
        of a drive.

        Args:
            None
        
        Returns:
            Uniform: A program node representing the uniform spatial modulation.
        
        ??? abstract "Background and Context"

            Fields give you local (single-atom) control over the many-body Rydberg Hamiltonian.

            They are a sum of one or more spatial modulations multiplied by a waveform:

            $$
            \\begin{align*}
            & F_{i}(t) = \sum_{\\alpha} C_{i}^{\\alpha}f_{\\alpha}(t) 
            \\\\
            & C_{i}^{\\alpha} \in \mathbb{R} 
            \\\\
            & f_{\\alpha}(t) \colon \mathbb{R} \\to \mathbb{R}
            \\end{align*}
            $$

            The $i$-th component of the field is used to generate the drive at the $i$-th site.

            Note that the drive is only applied if the $i$-th site is filled with an atom.

            You build fields in Bloqade by first specifying the spatial modulation followed by the waveform
            it should be multiplied by.

            In the case of a uniform spatial modulation, it can be interpreted as 
            a constant scaling factor where $C_{i}^{\\alpha} = 1.0$.

        ??? example "Examples"

            `uniform` can be accessed by first specifying the desired level coupling 
            followed by the field to begin constructing.

            ```python
            from bloqade import start
            geometry = start.add_position((0,0))
            coupling = geometry.rydberg
            uniform_rabi_amplitude = coupling.rabi.amplitude.uniform
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

            # Global vs. Local Detuning

            `uniform` and using [`location`][bloqade.builder.field.Field.location] where all atoms are targeted with a scaling of $1$ or [`scale`][bloqade.builder.field.Field.scale]
            with similar behavior will lead to identical behavior in emulation but can have subtle differences on hardware as [`location`][bloqade.builder.field.Field.location]
            and [`scale`][bloqade.builder.field.Field.scale] use a locally targeting laser while `uniform` uses a globally (all-atom) targeting laser.

        # Reachable Via
        
        You may reach the `uniform` property from the following properties:

        * [`detuning`][bloqade.builder.coupling.LevelCoupling.detuning]: Begin specifying the detuning field.
        * [`amplitude`][bloqade.builder.field.Rabi.amplitude]: Begin specifying the Rabi Amplitude field.
        * [`phase`][bloqade.builder.field.Rabi.phase]: Begin specifying the Rabi Phase field.

        # Next Possible Steps
        
        Next steps to build your program include choosing the waveform that
        will be multiplied with the spatial modulation.

        * [`linear(start, stop, duration)`][bloqade.builder.waveform.WaveformAttachable.linear]: to construct a linear waveform
        * [`constant(value, duration)`][bloqade.builder.waveform.WaveformAttachable.constant]: to construct a constant waveform
        * [`poly([coefficients], duration)`][bloqade.builder.waveform.WaveformAttachable.poly]: to construct a polynomial waveform
        * [`apply(waveform)`][bloqade.builder.waveform.WaveformAttachable.apply]: to apply a pre-defined waveform
        * [`piecewise_linear([durations], [values])`][bloqade.builder.waveform.WaveformAttachable.piecewise_linear]: to construct a piecewise linear waveform
        * [`piecewise_constant([durations], [values])`][bloqade.builder.waveform.WaveformAttachable.piecewise_constant]: to construct a piecewise constant waveform
        * [`fn(f(t,...))`][bloqade.builder.waveform.WaveformAttachable.fn]: to apply a function as a waveform
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
    ) -> "Location":
        """Address a a subset of atoms as part of defining the spatial modulation component of a drive
        with a unique scaling factor for each of them.

        Args:
            labels (Union[List[int], int]): A list of site indices or a single site index to target.
            scales (Union[List[ScalarType], ScalarType, None]): A list of scaling factors for each site or a single scaling factor to target all sites.

        Returns:
            Location: A program node representing the spatial modulation with unique scaling factors for some atoms.

        ??? abstract "Background and Context"

            Fields give you local (single-atom) control over the many-body Rydberg Hamiltonian.

            They are a sum of one or more spatial modulations multiplied by a waveform:

            $$
            \\begin{align*}
            & F_{i}(t) = \sum_{\\alpha} C_{i}^{\\alpha}f_{\\alpha}(t) 
            \\\\
            & C_{i}^{\\alpha} \in \mathbb{R} 
            \\\\
            & f_{\\alpha}(t) \colon \mathbb{R} \\to \mathbb{R}
            \\end{align*}
            $$

            The $i$-th component of the field is used to generate the drive at the $i$-th site.

            Note that the drive is only applied if the $i$-th site is filled with an atom.

            You build fields in Bloqade by first specifying the spatial modulation followed by the waveform
            it should be multiplied by.

            In the case of a spatial modulation produced by `location`, you can provide a unique scaling factor scaling factor $C_{i}^{\\alpha}$ for each OR some sites $i$ in the system.

        ??? example "Examples"

            We start by creating a simple program with 3 atoms targeting the Rydberg level coupling and
            we begin constructing the Rabi amplitude field:
            
            ```python
            from bloqade import start
            program = start.add_position([(0,0), (4,0), (8,0)]).rydberg.rabi.amplitude
            ```

            We can specify that we only want to target the first site with a scaling of $1.0$:
            ```python
            single_location_scaled = program.location(0)
            ```

            We may also specify that we want to target only the first site but with a different scaling:
            ```python
            custom_scaled_single_location = program.location(0, 0.5)
            ```

            We can also target a subset of the sites with a scaling of $1.0$:
            ```python
            multi_location_scaled = program.location([0, 2])
            ```

            And finally we can target a subset of sites with custom scaling coefficients:
            ```python
            custom_multi_location_scaled = program.location([0, 2], [0.5, 0.25])
            ```
        
        ??? warning "Potential Pitfalls"

            # Global vs. Local Detuning

            [`uniform`][bloqade.builder.field.Detuning.uniform] and using `location` where all atoms are targeted with a scaling of $1$ or [`scale`][bloqade.builder.field.Field.scale]
            with similar behavior in the construction of the Detuning field will lead to identical behavior in emulation but can have subtle differences on hardware as [`location`][bloqade.builder.field.Field.location]
            and [`scale`][bloqade.builder.field.Field.scale] use a locally targeting laser while `uniform` uses a globally (all-atom) targeting laser.

            # Number of Coefficients

            The number of coefficients you provide should be equal to the number of atoms in your program. The first coefficient will target the first atom, the second coefficient will target the second atom, and so on.

            # Hardware Differences

            While you can build fields of the following form in Bloqade for the Rabi Amplitude, Rabi Phase, and Detuning of the many-body Rydberg Hamiltonian:

            $$
            \\begin{align*}
            & F_{i}(t) = \sum_{\\alpha} C_{i}^{\\alpha}f_{\\alpha}(t) 
            \\\\
            & C_{i}^{\\alpha} \in \mathbb{R} 
            \\\\
            & f_{\\alpha}(t) \colon \mathbb{R} \\to \mathbb{R}
            \\end{align*}
            $$

            The hardware only supports the following configuration for the Detuning field:

            $$
            \\begin{align*}
            & \Delta_{i}(t) = \Delta_{1}(t) + c_{i} \Delta_{2}(t)
            \\\\
            & c_i \in [0, 1]
            \\\\
            & \Delta_{2}(t) \leq 0
            \\end{align*}
            $$

            Where $\Delta_{1}(t)$ is your global detuning (establishable via [`uniform`][bloqade.builder.field.Detuning.uniform]) and $\Delta_{2}(t)$ is your
            local detuning waveform with the spatial modulation $c_{i}$ establishable via [`location`][bloqade.builder.field.Detuning.location] or [`scale`][bloqade.builder.field.Detuning.scale].

            For the Rabi Amplitude and Rabi Phase fields the hardware only supports [`uniform`][bloqade.builder.field.Detuning.uniform]:

            $$
            \\begin{align*}
            & \Omega_{i}(t) = \Omega_{1}(t)
            \\\\
            & \phi_{i}(t) = \phi_{1}(t)
            \\end{align*}
            $$

        # Reachable Via

        You may reach the `location` property from the following properties:

        * [`detuning`][bloqade.builder.coupling.LevelCoupling.detuning]: Begin specifying the detuning field.
        * [`amplitude`][bloqade.builder.field.Rabi.amplitude]: Begin specifying the Rabi Amplitude field.
        * [`phase`][bloqade.builder.field.Rabi.phase]: Begin specifying the Rabi Phase field.

        # Next Possible Steps 

        Next steps to build your program include choosing the waveform that
        will be multiplied with the spatial modulation.

        * [`linear(start, stop, duration)`][bloqade.builder.waveform.WaveformAttachable.linear]: to construct a linear waveform
        * [`constant(value, duration)`][bloqade.builder.waveform.WaveformAttachable.constant]: to construct a constant waveform
        * [`poly([coefficients], duration)`][bloqade.builder.waveform.WaveformAttachable.poly]: to construct a polynomial waveform
        * [`apply(waveform)`][bloqade.builder.waveform.WaveformAttachable.apply]: to apply a pre-defined waveform
        * [`piecewise_linear([durations], [values])`][bloqade.builder.waveform.WaveformAttachable.piecewise_linear]: to construct a piecewise linear waveform
        * [`piecewise_constant([durations], [values])`][bloqade.builder.waveform.WaveformAttachable.piecewise_constant]: to construct a piecewise constant waveform
        * [`fn(f(t,...))`][bloqade.builder.waveform.WaveformAttachable.fn]: to apply a function as a waveform

        """
        return self._location(labels, scales)

    def scale(self, coeffs: Union[str, List[ScalarType]]) -> "Scale":
        """
        Address all the atoms as part of a spatial modulation but 
        with with a unique scaling factor for each of them.

        Args:
            coeffs (Union[str, List[ScalarType]]): A list of scaling factors for each atom or a variable to be assigned to later.

        Returns:
            Scale: A program node representing the spatial modulation with unique scaling factors for each atom.

        ??? abstract "Background and Context"

            Fields give you local (single-atom) control over the many-body Rydberg Hamiltonian.

            They are a sum of one or more spatial modulations multiplied by a waveform:

            $$
            \\begin{align*}
            & F_{i}(t) = \sum_{\\alpha} C_{i}^{\\alpha}f_{\\alpha}(t) 
            \\\\
            & C_{i}^{\\alpha} \in \mathbb{R} 
            \\\\
            & f_{\\alpha}(t) \colon \mathbb{R} \\to \mathbb{R}
            \\end{align*}
            $$

            The $i$-th component of the field is used to generate the drive at the $i$-th site.

            Note that the drive is only applied if the $i$-th site is filled with an atom.

            You build fields in Bloqade by first specifying the spatial modulation followed by the waveform
            it should be multiplied by.

            In the case of a spatial modulation produced by `scale`, it can be interpreted as providing a 
            unique scaling factor $C_{i}^{\\alpha}$ for each site $i$ in the system.

        
        ??? example "Examples"

            We start by creating a simple program with 3 atoms targeting the Rydberg level coupling and 
            we begin constructing the Rabi amplitude field:
            
            ```python
            from bloqade import start
            program = start.add_position([(0,0), (4,0), (8,0)]).rydberg.rabi.amplitude
            ```

            We can use a list of values to scale the subsequent waveform applied to each atom:

            ```python
            literally_scaled_program = program.scale([0.1, 0.2, 0.3])
            ```

            We can also use a variable that can then be assigned to at the end of program 
            construction. Bloqade requires the field definition be complete (has a 
            spatial modulation AND a waveform) before assignment is permitted.

            ```python
            variable_scaled_program = program.scale("scalings")
            variable_scaled_program.constant(1.0, 1.0).assign(a = [0.1, 0.2, 0.3])
            ```

            You may also perform batch assignment to the variable should you want to
            create multiple tasks with different scaling factors:

            ```python
            batch_scaled_program = program.scale("scalings")
            batch_scaled_program.constant(1.0, 1.0).batch_assign(a = [[0.1, 0.2, 0.3], [0.2, 0.3, 0.4], [0.3, 0.4, 0.5]])
            ```

        ??? info "Applications"

            * [Lattice Gauge Theory Simulation](https://queracomputing.github.io/bloqade-python-examples/latest/examples/example-6-lattice-gauge-theory/)

        ??? warning "Potential Pitfalls"

            # Global vs. Local Detuning

            [`uniform`][bloqade.builder.field.Detuning.uniform] and using [`location`][bloqade.builder.field.Field.location] where all atoms are targeted with a scaling of $1$ or `scale`
            with similar behavior in the construction of the Detuning field will lead to identical behavior in emulation but can have subtle differences on hardware as [`location`][bloqade.builder.field.Field.location]
            and `scale` use a locally targeting laser  while [`uniform`][bloqade.builder.field.Detuning.uniform] uses a globally (all-atom) targeting laser.

            # Number of Coefficients

            The number of coefficients you provide should be equal to the number of atoms in your program. The first coefficient will target the first atom, the second coefficient will target the second atom, and so on.

            # Hardware Differences

            While you can build fields of the following form in Bloqade for the Rabi Amplitude, Rabi Phase, and Detuning of the many-body Rydberg Hamiltonian:

            $$
            \\begin{align*}
            & F_{i}(t) = \sum_{\\alpha} C_{i}^{\\alpha}f_{\\alpha}(t) 
            \\\\
            & C_{i}^{\\alpha} \in \mathbb{R} 
            \\\\
            & f_{\\alpha}(t) \colon \mathbb{R} \\to \mathbb{R}
            \\end{align*}
            $$

            The hardware only supports the following configuration for the Detuning field:

            $$
            \\begin{align*}
            & \Delta_{i}(t) = \Delta_{1}(t) + c_{i} \Delta_{2}(t)
            \\\\
            & c_i \in [0, 1]
            \\\\
            & \Delta_{2}(t) \leq 0
            \\end{align*}
            $$

            Where $\Delta_{1}(t)$ is your global detuning (establishable via [`uniform`][bloqade.builder.field.Detuning.uniform]) and $\Delta_{2}(t)$ is your
            local detuning waveform with the spatial modulation $c_{i}$ establishable via [`location`][bloqade.builder.field.Detuning.location] or [`scale`][bloqade.builder.field.Detuning.scale].

            For the Rabi Amplitude and Rabi Phase fields the hardware only supports [`uniform`][bloqade.builder.field.Detuning.uniform]:

            $$
            \\begin{align*}
            & \Omega_{i}(t) = \Omega_{1}(t)
            \\\\
            & \phi_{i}(t) = \phi_{1}(t)
            \\end{align*}
            $$

        # Reachable Via

        You may reach the `scale` property from the following properties:

        * [`detuning`][bloqade.builder.coupling.LevelCoupling.detuning]: Begin specifying the detuning field.
        * [`amplitude`][bloqade.builder.field.Rabi.amplitude]: Begin specifying the Rabi Amplitude field.
        * [`phase`][bloqade.builder.field.Rabi.phase]: Begin specifying the Rabi Phase field.

        # Next Possible Steps 

        Next steps to build your program include choosing the waveform that
        will be multiplied with the spatial modulation.

        * [`linear(start, stop, duration)`][bloqade.builder.waveform.WaveformAttachable.linear]: to construct a linear waveform
        * [`constant(value, duration)`][bloqade.builder.waveform.WaveformAttachable.constant]: to construct a constant waveform
        * [`poly([coefficients], duration)`][bloqade.builder.waveform.WaveformAttachable.poly]: to construct a polynomial waveform
        * [`apply(waveform)`][bloqade.builder.waveform.WaveformAttachable.apply]: to apply a pre-defined waveform
        * [`piecewise_linear([durations], [values])`][bloqade.builder.waveform.WaveformAttachable.piecewise_linear]: to construct a piecewise linear waveform
        * [`piecewise_constant([durations], [values])`][bloqade.builder.waveform.WaveformAttachable.piecewise_constant]: to construct a piecewise constant waveform
        * [`fn(f(t,...))`][bloqade.builder.waveform.WaveformAttachable.fn]: to apply a function as a waveform

        """
        from bloqade.builder.spatial import Scale

        return Scale(coeffs, self)


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
            - `...amplitude.uniform`: Address all atoms in the field
            - `...amplitude.location(...)`: Scale atoms by their indices
            - `...amplitude.scale(...)`: Scale each atom with a value from a
                list or assign a variable name to be assigned later

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
            - `...amplitude.uniform`: Address all atoms in the field
            - `...amplitude.location(...)`: Scale atoms by their indices
            - `...amplitude.scale(...)`: Scale each atom with a value from a
                list or assign a variable name to be assigned later

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
