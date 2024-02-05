from decimal import Decimal
from bloqade.ir.visitor import BloqadeIRVisitor
from bloqade.ir import location
from bloqade.submission.ir.capabilities import QuEraCapabilities


class BasicLatticeValidation(BloqadeIRVisitor):
    """This visitor checks that the AtomArrangement is within the bounds of
    the lattice and that the number of sites is within the maximum number of sites.

    """

    def __init__(self, capabilities: QuEraCapabilities):
        self.capabilities = capabilities

    def generic_visit(self, node):
        # dispatch all AtomArrangement nodes to visit_register
        # otherwise dispatch to super
        if isinstance(node, location.AtomArrangement):
            self.visit_register(node)

        super().generic_visit(node)

    def visit_register(self, node: location.AtomArrangement):
        # default visitor for AtomArrangement

        height_max = self.capabilities.capabilities.lattice.area.height / Decimal(
            "1e-6"
        )
        width_max = self.capabilities.capabilities.lattice.area.width / Decimal("1e-6")
        number_sites_max = (
            self.capabilities.capabilities.lattice.geometry.number_sites_max
        )

        sites = []
        x_min = Decimal("inf")
        x_max = Decimal("-inf")
        y_min = Decimal("inf")
        y_max = Decimal("-inf")

        for location_info in node.enumerate():
            site = tuple(ele() for ele in location_info.position)
            sites.append(site)

            x_min = min(x_min, site[0])
            x_max = max(x_max, site[0])
            y_min = min(y_min, site[1])
            y_max = max(y_max, site[1])

        if len(sites) > number_sites_max:
            raise ValueError(
                "Too many sites in AtomArrangement, found "
                f"{len(sites)} but maximum is {number_sites_max}"
            )

        if x_max - x_min > width_max:
            raise ValueError(
                "AtomArrangement too wide, found "
                f"{x_max - x_min} but maximum is {width_max}"
            )

        if y_max - y_min > height_max:
            raise ValueError(
                "AtomArrangement too tall, found "
                f"{y_max - y_min} but maximum is {height_max}"
            )
