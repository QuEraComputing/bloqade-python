from beartype import beartype
from decimal import Decimal
from beartype.typing import Optional
from bloqade.ir.visitor import BloqadeIRVisitor
from bloqade.ir.control import field, pulse
from bloqade.submission.ir.parallel import ParallelDecoder
from bloqade.ir import analog_circuit, scalar


class GenerateLatticeSiteCoefficients(BloqadeIRVisitor):
    def __init__(self, parallel_decoder: Optional[ParallelDecoder] = None):
        self.n_sites = None
        self.parallel_decoder = parallel_decoder

    def post_spatial_modulation_visit(self):
        if self.parallel_decoder is None:
            # if we are not parallelizing, we don't need to do anything
            return

        # create a copy of the cluster site coefficients
        lattice_site_coefficients = list(self.lattice_site_coefficients)
        # insert the cluster site coefficients into the parallelized
        # lattice site coefficients
        self.lattice_site_coefficients = []
        for cluster_site_info in self.parallel_decoder.mapping:
            self.lattice_site_coefficients.append(
                lattice_site_coefficients[cluster_site_info.cluster_location_index]
            )

    # We don't need to visit UniformModulation because local detuning
    # UniformModulation is merged into global detuning

    def visit_field_ScaledLocations(self, node: field.ScaledLocations):
        for i in range(self.n_sites):
            value = node.value.get(field.Location(i), scalar.Literal(0))
            self.lattice_site_coefficients.append(value)

    def visit_field_AssignedRunTimeVector(self, node: field.AssignedRunTimeVector):
        self.lattice_site_coefficients = list(map(Decimal, map(str, node.value)))

    def visit_field_Field(self, node: field.Field):
        (local_detuning_spatial_modulation,) = node.drives.keys() - {field.Uniform}
        self.visit(local_detuning_spatial_modulation)
        self.post_spatial_modulation_visit()

    def visit_pulse_Pulse(self, node: pulse.Pulse):
        self.visit(node.fields[pulse.detuning])

    def visit_analog_circuit_AnalogCircuit(self, node: analog_circuit.AnalogCircuit):
        self.n_sites = node.register.n_sites
        self.visit(node.sequence)

    # needs to be an instance of analog_circuit.AnalogCircuit
    # because we need to know the number of sites
    @beartype
    def emit(self, node: analog_circuit.AnalogCircuit):
        self.visit(node)
        return self.lattice_site_coefficients
