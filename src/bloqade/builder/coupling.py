from bloqade.builder.base import Builder
from bloqade.builder.field import Rabi, Detuning


class LevelCoupling(Builder):
    @property
    def detuning(
        self,
    ) -> Detuning:
        """
        Specify the [`Detuning`][bloqade.builder.field.Detuning] [`Field`][bloqade.builder.field.Field] of your program. You will be able to specify the spatial modulation afterwards.

        Args:
            None

        Returns:
            [`Detuning`][bloqade.builder.field.Detuning]: A program node representing the detuning field.

        ??? abstract "Background and Context"

            In the Many-Body Rydberg Hamiltonian:

            $$
            \\frac{\mathcal{H}(t)}{\hbar} = \sum_j \\frac{\Omega_j(t)}{2} \left( e^{i \phi_j(t) } | g_j \\rangle  \langle r_j | + e^{-i \phi_j(t) } | r_j \\rangle  \langle g_j | \\right) - \sum_j \Delta_j(t) \hat{n}_j + \sum_{j < k} V_{jk} \hat{n}_j \hat{n}_k.
            $$

            The detuning is specified by the term $\Delta_j(t)$ and specifies how off-resonant the laser being applied to the atoms is from the atomic energy transition, which is driven by the Rabi frequency $\Omega_j(t)$.

            The detuning is described by a field, which is the summation of one or more drives, with the drive being the sum of a waveform and spatial modulation:

            $$
            \sum_j \Delta_j(t)  = \sum_j \sum_a C^{a}_{j} f_{a}(t)
            $$

            Note that the spatial modulation $C_{j}$ scales how much of the detuning waveform is experienced by the atom at site $j$. You can specify the scaling that all atoms feel to be
            identical (global detuning) or you can specify different scaling for different atoms (local detuning).

        ??? example "Examples"

            ```python
            from bloqade import start

            # specify geometry, in this case just one atom
            geometry = start.add_position((0,0))
            # specify your coupling (either `rydberg` or `hyperfine`)
            coupling = geometry.rydberg
            # Begin specifying your detuning
            coupling.detuning
            ```
            Alternatively you may start with building your Rabi field and then reach the ability to build your detuning like so:

            ```python
            from bloqade import start
            geometry = start.add_position((0,0))
            coupling = geometry.rydberg
            rabi_field = coupling.rabi.amplitude.uniform.constant(duration = 1.0, value = 1.0)
            detuning = rabi_field.detuning
            ```


        ??? info "Applications"

            * [Single Qubit Floquet Dynamics](https://queracomputing.github.io/bloqade-python-examples/latest/examples/example-1-floquet/)
            * [Two Qubit Adiabatic Sweep](https://queracomputing.github.io/bloqade-python-examples/latest/examples/example-2-two-qubit-adiabatic/)
            * [1D Z2 State Preparation](https://queracomputing.github.io/bloqade-python-examples/latest/examples/example-3-time-sweep/)
            * [2D State Preparation](https://queracomputing.github.io/bloqade-python-examples/latest/examples/example-3-2d-ordered-state/)
            * [Quantum Scar Dynamics](https://queracomputing.github.io/bloqade-python-examples/latest/examples/example-4-quantum-scar-dynamics/)
            * [Solving the Maximal Independent Set Problem on defective King Graph](https://queracomputing.github.io/bloqade-python-examples/latest/examples/example-5-MIS-UDG/)

        ??? warning "Potential Pitfalls"

            Bloqade allows you to build a field for the Detuning in the form of:

            $$
            \sum_j \Delta_j(t)  = \sum_j \sum_a C^{a}_{j} f_{a}(t)
            $$

            Where your field can contain multiple drives.

            In reality the hardware only supports the following configuration:

            $$
            \Delta_{i}(t) = \Delta_{1}(t) + c_{i} \Delta_{2}(t)
            $$

            $$
            c_i \in [0, 1]
            $$

            $$
            \Delta_{2}(t) \leq 0
            $$

            Where $\Delta_{1}(t)$ is your global detuning (establishable via [`uniform`][bloqade.builder.field.Detuning.uniform]) and $\Delta_{2}(t)$ is your
            local detuning waveform with the spatial modulation $c_{i}$ establishable via [`location`][bloqade.builder.field.Detuning.location] or [`scale`][bloqade.builder.field.Detuning.scale].

        # Next Possible Steps

        You may continue building your program via:

        - [`uniform`][bloqade.builder.field.Detuning.uniform]: To address all atoms in the field
        - [`location(locations, scales)`][bloqade.builder.field.Detuning.location]: To address atoms at specific
            locations via indices
        - [`scale(coeffs)`][bloqade.builder.field.Detuning.scale]: To address all atoms with an individual scale factor

        """

        return Detuning(self)

    @property
    def rabi(self) -> Rabi:
        """
        Specify the complex-valued [`Rabi`][bloqade.builder.field.Rabi]
        field of your program.

        The Rabi field is composed of a real-valued Amplitude and Phase field.

        - Next possible steps to build your program are
          creating the [`RabiAmplitude`][bloqade.builder.field.RabiAmplitude] field
          and [`RabiPhase`][bloqade.builder.field.RabiAmplitude] field of the field:
            - `...rabi.amplitude`: To create the Rabi amplitude field
            - `...rabi.phase`: To create the Rabi phase field

        """

        return Rabi(self)


class Rydberg(LevelCoupling):
    """
    This node represent level coupling of rydberg state.

    Examples:

        - To reach the node from the start node:

        >>> node = bloqade.start.rydberg
        >>> type(node)
        <class 'bloqade.builder.coupling.Rydberg'>

        - Rydberg level coupling have two reachable field nodes:

            - detuning term (See also [`Detuning`][bloqade.builder.field.Detuning])
            - rabi term (See also [`Rabi`][bloqade.builder.field.Rabi])

        >>> ryd_detune = bloqade.start.rydberg.detuning
        >>> ryd_rabi = bloqade.start.rydberg.rabi

    """

    def __bloqade_ir__(self):
        from bloqade.ir.control.sequence import rydberg

        return rydberg


class Hyperfine(LevelCoupling):
    """
    This node represent level coupling between hyperfine state.

    Examples:

        - To reach the node from the start node:

        >>> node = bloqade.start.hyperfine
        >>> type(node)
        <class 'bloqade.builder.coupling.Hyperfine'>

        - Hyperfine level coupling have two reachable field nodes:

            - detuning term (See also [`Detuning`][bloqade.builder.field.Detuning])
            - rabi term (See also [`Rabi`][bloqade.builder.field.Rabi])

        >>> hyp_detune = bloqade.start.hyperfine.detuning
        >>> hyp_rabi = bloqade.start.hyperfine.rabi

    """

    def __bloqade_ir__(self):
        from bloqade.ir.control.sequence import hyperfine

        return hyperfine
