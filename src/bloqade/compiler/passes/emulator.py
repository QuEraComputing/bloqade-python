from bloqade.compiler.analysis.common import ScanChannels, ScanVariables
from bloqade.compiler.codegen.emulator_ir import EmulatorProgramCodeGen
from bloqade.compiler.rewrite.common import (
    AddPadding,
    FlattenCircuit,
    AssignBloqadeIR,
    AssignToLiteral,
    Canonicalizer,
)


def flatten(circuit):
    level_couplings = ScanChannels().scan(circuit)
    circuit = AddPadding(level_couplings).visit(circuit)
    return FlattenCircuit(level_couplings).visit(circuit)


def assign(assignments, circuit):
    circuit = AssignBloqadeIR(assignments).emit(circuit)
    assignment_analysis = ScanVariables().scan(circuit)

    if not assignment_analysis.is_assigned:
        missing_vars = assignment_analysis.scalar_vars.union(
            assignment_analysis.vector_vars
        )
        raise ValueError(
            "Missing assignments for variables:\n"
            + ("\n".join(f"{var}" for var in missing_vars))
            + "\n"
        )

    return Canonicalizer().visit(AssignToLiteral().visit(circuit))


def generate_emulator_ir(circuit, blockade_radius, use_hyperfine):
    return EmulatorProgramCodeGen(
        blockade_radius=blockade_radius, use_hyperfine=use_hyperfine
    ).emit(circuit)
