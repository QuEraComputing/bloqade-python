from beartype import beartype
from bloqade.ir import analog_circuit
import bloqade.ir.control.field as field
import bloqade.ir.control.pulse as pulse
import bloqade.ir.control.sequence as sequence

from bloqade.ir.visitor import BloqadeIRVisitor


class ValidateChannels(BloqadeIRVisitor):
    """Checks to make sure the given sequence can be compiled to hardware.

    This check looks at the spatial modulations and the level coupling
    to determine if the sequence can be compiled to hardware.

    """

    def __init__(self):
        self.field_name = None

    def visit_sequence_Sequence(self, node: sequence.Sequence) -> None:
        for level_coupling, pulse_expr in node.pulses.items():
            if level_coupling == sequence.hyperfine:
                raise ValueError("Hyperfine coupling not supported by AHS")

            self.visit(pulse_expr)

    def visit_pulse_Pulse(self, node: pulse.Pulse) -> None:
        for field_name, field_expr in node.fields.items():
            self.field_name = field_name
            self.visit(field_expr)

    def visit_field_Field(self, node: field.Field) -> None:
        non_uniform_modulations = node.drives.keys() - {field.Uniform}
        spatial_modulation_str = "\n\n".join(map(str, non_uniform_modulations))

        if self.field_name in [pulse.rabi.amplitude, pulse.rabi.phase]:
            if non_uniform_modulations:
                raise ValueError(
                    f"{self.field_name} can only have uniform spatial modulation, "
                    f"found:\n\n{spatial_modulation_str}"
                )
        else:
            if len(non_uniform_modulations) > 1:
                raise ValueError(
                    f"{self.field_name} can only have one non-uniform spatial "
                    f"modulation, found:\n\n{spatial_modulation_str}"
                )

            (non_uniform_modulation,) = non_uniform_modulations
            self.visit(non_uniform_modulation)

    def visit_field_ScaledLocations(self, node: field.ScaledLocations) -> None:
        for loc in node.value.keys():
            if loc.value >= self.n_sites:
                raise ValueError(
                    "location index out of range: "
                    f"found {loc.value} with a total number of sites: {self.n_sites}."
                    f"Error found in the {self.field_name} field "
                    f"with spatial modulation:\n\n{self.spatial_modulations}"
                )

    def visit_field_AssignedRunTimeVector(
        self, node: field.AssignedRunTimeVector
    ) -> None:
        if len(node.value) != self.n_sites:
            raise ValueError(
                "length of runtime vector does not match number of sites in the "
                f"register. expected {self.n_sites}, found {len(node.value)} for "
                f"the {self.field_name} field with spatial modulation:"
                f"\n\n{self.spatial_modulations}"
            )

    def visit_analog_circuit_AnalogCircuit(
        self, node: analog_circuit.AnalogCircuit
    ) -> None:
        self.n_sites = node.register.n_sites
        self.visit(node.sequence)

    # needs to be an instance of analog_circuit.AnalogCircuit
    # because we need to know the number of sites
    @beartype
    def scan(self, node: analog_circuit.AnalogCircuit) -> None:
        self.visit(node)
