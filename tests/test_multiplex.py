from bloqade.atoms import Square
from bloqade.ir.program import Program
from bloqade.codegen.quera_hardware import SchemaCodeGen

from bloqade.ir import (
    rydberg,
    detuning,
    Sequence,
    Uniform,
    Linear,
    ScaledLocations,
)


# create lattice
lattice = Square(4)

# create some test sequence
seq = Sequence(
    {
        rydberg: {
            detuning: {
                Uniform: Linear(start=1.0, stop=5.2, duration=3.0),
                ScaledLocations({1: 1.0, 2: 2.0, 3: 3.0, 4: 4.0}): Linear(
                    start=1.0, stop=5.2, duration=3.0
                ),
            },
        }
    }
)


prog = Program(lattice, seq)

cluster_spacing = 4.0

# can remove multiplex_enabled flag in favor of checking presence of mapping attribute
multiplexed_prog = Program(lattice, seq, cluster_spacing=2.5)
# multiplexed_prog = multiplex_program(prog, cap, cluster_spacing)

# call codegen
generated_schema = SchemaCodeGen().emit(100, multiplexed_prog)
