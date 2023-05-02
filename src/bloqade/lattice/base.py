from ..builder import RydbergBuilder, HyperfineBuilder


class Lattice:
    def apply(self, seq):
        """apply a sequence to the lattice."""
        from ..task import Program

        return Program(self, seq)

    @property
    def rydberg(self) -> RydbergBuilder:
        """start building pulses for Rydberg coupling

        ### Example

        ```python-repl
        >>> lattice.Square(3).rydberg.detuning.glob.apply(Linear(start=1.0, stop="x", duration=3.0))
        ```
        """
        return RydbergBuilder(self)

    @property
    def hyperfine(self) -> HyperfineBuilder:
        """start building pulses for hyperfine coupling

        ### Example

        >>> lattice.Square(3).hyperfine.detuning.glob.apply(Linear(start=1.0, stop="x", duration=3.0))
        """
        return HyperfineBuilder(self)
