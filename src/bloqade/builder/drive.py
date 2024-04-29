from bloqade.builder.coupling import Rydberg, Hyperfine


class Drive:
    @property
    def rydberg(self) -> Rydberg:
        """
        Address the Rydberg level coupling in your program.

        Args:
          None

        Returns:
          Rydberg: Rydberg level coupling program node.

        ??? abstract "Background and Context"

            QuEra's neutral atom QPU *Aquila* use Rb-87 atoms as qubits.
            As a result Bloqade's simulations are based on the Rb-87 atoms energy level structure.

            There are three energy levels of interest in the atoms:

            * Two hyperfine levels
                * $|0\\rangle$ and $|1\\rangle$
            * One Rydberg level
                * $|r\\rangle$

            The transition between energy levels your subsequently constructed field will address is known as a coupling.

            `rydberg` allows you to specify that a field will address the coupling between $|0\\rangle$ and $|r\\rangle$.

        ??? example "Examples"

            We begin by defining an atom geometry with just a single atom:

            ```python
            from bloqade import start
            program = start.add_position((0,0))
            ```

            We can then specify the Rydberg coupling:
            ```python
            target_rydberg_coupling = program.rydberg
            ```

            Alternatively we can build a pulse sequence independent of the geometry by skipping the need to `add_position`'s:
            ```python
            pulse_sequence = start.rydberg
            ```

            It is also possible to select the Rydberg level coupling directly from any predefined geometry in Bloqade:
            ```python
            from bloqade.atom_arrangement import Kagome
            program = Kagome(2).rydberg
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

            # Shifted Couplings

            If only the Rydberg coupling is specified in your program via `rydberg` you will be addressing the
            coupling between $|0\\rangle$ and $|r\\rangle$. However if your program also targets the hyperfine coupling
            via [`hyperfine`][bloqade.builder.drive.Drive.hyperfine], `rydberg` will now address the coupling between
            $|1\\rangle$ and $|r\\rangle$ while [`hyperfine`][bloqade.builder.drive.Drive.hyperfine] will address the
            coupling between $|0\\rangle$ and $|1\\rangle$.


        # Reachable Via

        You can reach `rydberg` from:

        * [`start`][bloqade.ir.start] If you do this you will be constructing a pulse sequence which can then be later applied to a geometry.
        * [`add_position`][bloqade.atom_arrangement.AtomArrangement.add_position] adding a position to the atom geometry.
        * [`apply_defect_count`][bloqade.atom_arrangement.AtomArrangement.apply_defect_count] applying a number of defects to the atom geometry.
        * [`apply_defect_density`][bloqade.atom_arrangement.AtomArrangement.apply_defect_density] applying defects to the atom geometry with a certain probability.
        * [`scale`][bloqade.atom_arrangement.AtomArrangement.scale] scaling the atom geometry.

        * Atom Geometries
            * [`Kagome`][bloqade.atom_arrangement.Kagome]
            * [`Square`][bloqade.atom_arrangement.Square]
            * [`Triangular`][bloqade.atom_arrangement.Triangular]
            * [`Honeycomb`][bloqade.atom_arrangement.Honeycomb]
            * [`Lieb`][bloqade.atom_arrangement.Lieb]
            * [`Chain`][bloqade.atom_arrangement.Chain]
            * [`ListOfLocations`][bloqade.ir.location.location.ListOfLocations]


        # Next Possible Steps

        You can now specify the field you would like to build for the Rydberg coupling.

        * [`rabi`][bloqade.builder.coupling.Rydberg.rabi] for the complex-valued Rabi field
        * [`detuning`][bloqade.builder.coupling.Rydberg.detuning] for the detuning field

        """
        return Rydberg(self)

    @property
    def hyperfine(self) -> Hyperfine:
        """
        Address the Rydberg level coupling in your program.

        Args:
          None

        Returns:
          Rydberg: Rydberg level coupling program node.

        ??? abstract "Background and Context"

            QuEra's neutral atom QPU *Aquila* use Rb-87 atoms as qubits.
            As a result Bloqade's simulations are based on the Rb-87 atoms structure.

            There are three energy levels of interest in the atoms:

            * Two hyperfine levels
                * $|0\\rangle$ and $|1\\rangle$
            * One Rydberg level
                * $|r\\rangle$

            The transition between energy levels your subsequently constructed field will address is known as a coupling.

            `hyperfine` allows you to specify that a field will address the coupling between $|0\\rangle$ and $|1\\rangle$.

        ??? example "Examples"

            We begin by defining an atom geometry with just a single atom:

            ```python
            from bloqade import start
            program = start.add_position((0,0))
            ```

            We can then specify the hyperfine coupling:
            ```python
            target_rydberg_coupling = program.hyperfine
            ```

            Alternatively we can build a pulse sequence independent of the geometry by skipping the need to `add_position`'s:
            ```python
            pulse_sequence = start.hyperfine
            ```

            It is also possible to select the Rydberg level coupling directly from any predefined geometry in Bloqade:
            ```python
            from bloqade.atom_arrangement import Kagome
            program = Kagome(2).hyperfine
            ```

        ??? warning "Potential Pitfalls"

            # Shifted Couplings

            If only the Rydberg coupling is specified in your program via [`rydberg`][bloqade.builder.drive.Drive.rydberg] you will be addressing the
            coupling between $|0\\rangle$ and $|r\\rangle$. However if your program also targets the hyperfine coupling
            via `hyperfine`, [`rydberg`][bloqade.builder.drive.Drive.rydberg] will now address the coupling between
            $|1\\rangle$ and $|r\\rangle$ while `hyperfine` will address the
            coupling between $|0\\rangle$ and $|1\\rangle$.

            If only hyperfine is present in the program, you will still just be addressing the coupling between $|0\\rangle$ and $|1\\rangle$.

            # Hardware Differences

            Current hardware does not support addressing the hyperfine coupling. However, it is still emulatable in Bloqade.


        # Reachable Via

        You can reach `hyperfine` from:

        * [`start`][bloqade.ir.start] If you do this you will be constructing a pulse sequence which can then be later applied to a geometry.
        * [`add_position`][bloqade.atom_arrangement.AtomArrangement.add_position] adding a position to the atom geometry.
        * [`apply_defect_count`][bloqade.atom_arrangement.AtomArrangement.apply_defect_count] applying a number of defects to the atom geometry.
        * [`apply_defect_density`][bloqade.atom_arrangement.AtomArrangement.apply_defect_density] applying defects to the atom geometry with a certain probability.
        * [`scale`][bloqade.atom_arrangement.AtomArrangement.scale] scaling the atom geometry.

        * Atom Geometries
            * [`Kagome`][bloqade.atom_arrangement.Kagome]
            * [`Square`][bloqade.atom_arrangement.Square]
            * [`Triangular`][bloqade.atom_arrangement.Triangular]
            * [`Honeycomb`][bloqade.atom_arrangement.Honeycomb]
            * [`Lieb`][bloqade.atom_arrangement.Lieb]
            * [`Chain`][bloqade.atom_arrangement.Chain]
            * [`ListOfLocations`][bloqade.ir.location.location.ListOfLocations]


        # Next Possible Steps

        You can now specify the field you would like to build for the Rydberg coupling.

        * [`rabi`][bloqade.builder.coupling.Rydberg.rabi] for the complex-valued Rabi field
        * [`detuning`][bloqade.builder.coupling.Rydberg.detuning] for the detuning field

        """
        return Hyperfine(self)
