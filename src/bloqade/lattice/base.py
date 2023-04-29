from ..builder import RydbergBuilder, HyperfineBuilder


class Lattice:
    def run(self, seq):
        from ..task import Program

        return Program(self, seq)

    @property
    def rydberg(self) -> RydbergBuilder:
        return RydbergBuilder(self)

    @property
    def hyperfine(self) -> HyperfineBuilder:
        return HyperfineBuilder(self)
