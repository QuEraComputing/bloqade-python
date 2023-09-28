from bloqade.builder.base import Builder
from bloqade.builder.sequence_builder import SequenceBuilder
from bloqade.builder.drive import Drive
from bloqade.ir.control.sequence import Sequence
from beartype import beartype


class ProgramStart(Drive, Builder):
    """
    ProgramStart is the base class for a starting/entry node for building a program.
    """

    @beartype
    def apply(self, sequence: Sequence) -> SequenceBuilder:
        """
        - Apply a pre-built sequence to a program.
        - This allows you to build a program independent of any geoemetry
          and then `apply` the program to said geometry. Or, if you have a 
          program you would like to try on multiple geometries you can 
          trivially do so with this.
        - From here you can now:
            - |_ ...assign(assignments).bloqade: select the bloqade local emulator backend
            - |_ ...assign(assignments).braket: select braket local emulator or QuEra hardware
            - |_ ...assign(assignments).device(specifier_string): select backend by specifying a string
        - Assign multiple values to a single variable for a parameter sweep:
            - |_ ...assign(assignments).batch_assign(assignments): 
        - Parallelize the program register, duplicating the geometry and waveform sequence to take advantage of all available
          space/qubits on the QPU:
            - |_ ...assign(assignments).parallelize(cluster_spacing)
        - Defer value assignment of certain variables to runtime:
            - |_ ...assign(assignments).args([previously_defined_vars])

        Example Usage:
        ```
        >>> from numpy import pi
        >>> seq = start.rydberg.rabi.amplitude.constant(2.0 * pi, 4.5)
        # choose a geometry of interest to apply the program on
        >>> from bloqade.atom_arrangement import Chain, Kagome
        >>> complete_program = Chain(10).apply(seq)
        # you can .apply to as many geometries as you like
        >>> another_complete_program = Kagome(3).apply(seq)
        ```
        """
        return SequenceBuilder(sequence, self)
