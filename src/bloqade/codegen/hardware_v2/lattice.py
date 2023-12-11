from bloqade.ir.location import location
from bloqade.ir import analog_circuit
from bloqade.submission.ir.parallel import ClusterLocationInfo, ParallelDecoder
import numpy as np
from decimal import Decimal


class GenerateLattice:
    def __init__(self, capabilities=None):
        self.capabilities = capabilities
        self.parallel_decoder = None

    def generic_visit(self, node):
        # dispatch all AtomArrangement nodes to visit_register
        # otherwise dispatch to super
        if isinstance(node, location.AtomArrangement):
            self.visit_register(node)

        super().generic_visit(node)

    def visit_register(self, node: location.AtomArrangement):
        # default visitor for AtomArrangement
        self.sites = []
        self.filling = []

        for location_info in node.enumerate():
            site = tuple(ele(**self.assignments) for ele in location_info.position)
            self.sites.append(site)
            self.filling.append(location_info.filling.value)

    def visit_location_ParallelRegister(self, node: location.ParallelRegister):
        from bloqade.ir.location.location import ParallelRegisterInfo

        info = ParallelRegisterInfo(node)

        if self.capabilities is None:
            raise NotImplementedError(
                "Cannot parallelize register without device capabilities."
            )

        height_max = self.capabilities.capabilities.lattice.area.height / Decimal(
            "1e-6"
        )
        width_max = self.capabilities.capabilities.lattice.area.width / Decimal("1e-6")
        number_sites_max = (
            self.capabilities.capabilities.lattice.geometry.number_sites_max
        )

        register_filling = np.asarray(info.register_filling)

        register_locations = np.asarray(
            [[s() for s in location] for location in info.register_locations]
        )
        register_locations = register_locations - register_locations.min(axis=0)

        shift_vectors = np.asarray(
            [[s() for s in shift_vector] for shift_vector in info.shift_vectors]
        )

        # build register by stack method because
        # shift_vectors might not be rectangular
        c_stack = [(0, 0)]
        visited = set([(0, 0)])
        mapping = []
        global_site_index = 0
        sites = []
        filling = []
        while c_stack:
            if len(mapping) + len(info.register_locations) > number_sites_max:
                break

            cluster_index = c_stack.pop()

            shift = (
                shift_vectors[0] * cluster_index[0]
                + shift_vectors[1] * cluster_index[1]
            )

            new_register_locations = register_locations + shift

            # skip clusters that fall out of bounds
            if (
                np.any(new_register_locations < 0)
                or np.any(new_register_locations[:, 0] > width_max)
                or np.any(new_register_locations[:, 1] > height_max)
            ):
                continue

            new_cluster_indices = [
                (cluster_index[0] + 1, cluster_index[1]),
                (cluster_index[0], cluster_index[1] + 1),
                (cluster_index[0] - 1, cluster_index[1]),
                (cluster_index[0], cluster_index[1] - 1),
            ]

            for new_cluster_index in new_cluster_indices:
                if new_cluster_index not in visited:
                    visited.add(new_cluster_index)
                    c_stack.append(new_cluster_index)

            for cluster_location_index, (loc, filled) in enumerate(
                zip(new_register_locations[:], register_filling)
            ):
                site = tuple(loc)
                sites.append(site)
                filling.append(filled)

                mapping.append(
                    ClusterLocationInfo(
                        cluster_index=cluster_index,
                        global_location_index=global_site_index,
                        cluster_location_index=cluster_location_index,
                    )
                )

                global_site_index += 1

        self.sites = sites
        self.filling = filling
        self.parallel_decoder = ParallelDecoder(mapping=mapping)

    def visit_analog_circuit_AnalogCircuit(self, node: analog_circuit.AnalogCircuit):
        self.visit(node.register)

    def emit(self, node):
        self.visit(node)

        return self.sites, self.filling, self.parallel_decoder
