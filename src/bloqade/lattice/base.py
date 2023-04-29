from ..builder import RydbergBuilder, HyperfineBuilder

class Lattice:
    
    def run(self, seq):
        from ..task import Program
        return Program(self, seq)

    @property
    def rydberg(self) -> Builder:
        return Builder(self)

    @property
    def hyperfine(self) -> Builder:
        return Builder(self)
