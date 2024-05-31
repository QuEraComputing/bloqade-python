"""
Module for parsing and displaying quantum computing program components using the bloqade library.
"""

from beartype.typing import Union, TYPE_CHECKING
import bloqade.ir as ir
from bloqade.visualization import display_builder

if TYPE_CHECKING:
    from bloqade.ir import AtomArrangement, ParallelRegister, Sequence
    from bloqade.ir.analog_circuit import AnalogCircuit
    from bloqade.ir.routine.base import Routine
    from bloqade.builder.base import Builder


class ParseRegister:
    """
    A class providing functionality to parse the arrangement of atoms in the program.

    Example:

    ```python
    >>> class MyBuilder(ParseRegister):
    ...     pass
    >>> builder = MyBuilder()
    >>> atom_arrangement = builder.parse_register()
    ```
    """

    def parse_register(self: "Builder") -> Union["AtomArrangement", "ParallelRegister"]:
        """
        Parse the arrangement of atoms in the program.

        Returns:
            Union[AtomArrangement, ParallelRegister]: The parsed atom arrangement or parallel register.

        Raises:
            ValueError: If the register cannot be parsed.
        """
        from bloqade.builder.parse.builder import Parser

        return Parser().parse_register(self)


class ParseSequence:
    """
    A class providing functionality to parse the pulse sequence part of the program.

    Example:

    ```python
    >>> class MyBuilder(ParseSequence):
    ...     pass
    >>> builder = MyBuilder()
    >>> sequence = builder.parse_sequence()
    ```
    """

    def parse_sequence(self: "Builder") -> "Sequence":
        """
        Parse the pulse sequence part of the program.

        Returns:
            Sequence: The parsed pulse sequence.

        Raises:
            ValueError: If the sequence cannot be parsed.
        """
        from bloqade.builder.parse.builder import Parser

        return Parser().parse_sequence(self)


class ParseCircuit:
    """
    A class providing functionality to parse the analog circuit from the program.

    Example:

    ```python
    >>> class MyBuilder(ParseCircuit):
    ...     pass
    >>> builder = MyBuilder()
    >>> analog_circuit = builder.parse_circuit()
    ```
    """

    def parse_circuit(self: "Builder") -> "AnalogCircuit":
        """
        Parse the analog circuit from the program.

        Returns:
            AnalogCircuit: The parsed analog circuit.

        Raises:
            ValueError: If the circuit cannot be parsed.
        """
        from bloqade.builder.parse.builder import Parser

        return Parser().parse_circuit(self)


class ParseRoutine:
    """
    A class providing functionality to parse the program and return a Routine object.

    Example:

    ```python
    >>> class MyBuilder(ParseRoutine):
    ...     pass
    >>> builder = MyBuilder()
    >>> routine = builder.parse()
    ```
    """

    def parse(self: "Builder") -> "Routine":
        """
        Parse the program to return a Routine object.

        Returns:
            Routine: The parsed routine object.

        Raises:
            ValueError: If the routine cannot be parsed.
        """
        from bloqade.builder.parse.builder import Parser

        return Parser().parse(self)


class Parse(ParseRegister, ParseSequence, ParseCircuit, ParseRoutine):
    """
    A composite class inheriting from ParseRegister, ParseSequence, ParseCircuit, and ParseRoutine.
    Provides a unified interface for parsing different components of the program.
    """

    @property
    def n_atoms(self: "Builder") -> int:
        """
        Return the number of atoms in the program.

        Returns:
            int: The number of atoms in the parsed register.

        Raises:
            ValueError: If the register type is unsupported.

        Note:
            If the register is of type ParallelRegister, the number of atoms is extracted from its internal register.

        Example:

        ```python
        >>> class MyBuilder(Parse):
        ...     pass
        >>> builder = MyBuilder()
        >>> n_atoms = builder.n_atoms
        ```
        """
        register = self.parse_register()

        if isinstance(register, ir.location.ParallelRegister):
            return register._register.n_atoms
        else:
            return register.n_atoms


class Show:
    """
    A mixin class providing functionality to display the builder with given arguments and batch ID.
    """

    def show(self, *args, batch_id: int = 0):
        """
        Display the current program being defined with the given arguments and batch ID.

        Args:
            *args: Additional arguments for display.
            batch_id (int, optional): The batch ID to be displayed. Defaults to 0.

        Note:
            This method uses the `display_builder` function to render the builder's state.

        Example:

        ```python
        >>> class MyBuilder(Show):
        ...     pass
        >>> builder = MyBuilder()
        >>> builder.show()
        >>> builder.show(batch_id=1)
        >>> builder.show('arg1', 'arg2', batch_id=2)
        ```
        """
        display_builder(self, batch_id, *args)
