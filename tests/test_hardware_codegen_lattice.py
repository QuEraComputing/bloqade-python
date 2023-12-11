from decimal import Decimal

import pytest
from bloqade import cast
from bloqade.ir.location import ListOfLocations, ParallelRegister
from bloqade.codegen.hardware_v2.lattice import GenerateLattice
from bloqade.submission.capabilities import get_capabilities
from bloqade.submission.ir.parallel import ParallelDecoder, ClusterLocationInfo
from bloqade.ir.analog_circuit import AnalogCircuit
from bloqade.ir.control.sequence import Sequence


def test():
    lattice = ListOfLocations().add_position((0, 0)).add_position((0, 6), filling=False)

    capabilities = get_capabilities()

    capabilities.capabilities.lattice.area.height = Decimal("13.0e-6")
    capabilities.capabilities.lattice.area.width = Decimal("13.0e-6")
    capabilities.capabilities.lattice.geometry.number_sites_max = 4

    circuit = AnalogCircuit(lattice, Sequence({}))

    ahs_lattice_data = GenerateLattice(capabilities).emit(circuit)

    assert ahs_lattice_data.sites == [
        (Decimal("0.0"), Decimal("0.0")),
        (Decimal("0.0"), Decimal("6.0")),
    ]
    assert ahs_lattice_data.filling == [1, 0]
    assert ahs_lattice_data.parallel_decoder is None

    parallel_lattice = ParallelRegister(lattice, cast(5))

    with pytest.raises(ValueError):
        ahs_lattice_data = GenerateLattice().emit(parallel_lattice)

    ahs_lattice_data = GenerateLattice(capabilities).emit(parallel_lattice)

    assert ahs_lattice_data.sites == [
        (Decimal("0.0"), Decimal("0.0")),
        (Decimal("0.0"), Decimal("6.0")),
        (Decimal("5.0"), Decimal("0.0")),
        (Decimal("5.0"), Decimal("6.0")),
    ]
    assert ahs_lattice_data.filling == [1, 0, 1, 0]
    assert ahs_lattice_data.parallel_decoder == ParallelDecoder(
        [
            ClusterLocationInfo(
                cluster_index=(0, 0), global_location_index=0, cluster_location_index=0
            ),
            ClusterLocationInfo(
                cluster_index=(0, 0), global_location_index=1, cluster_location_index=1
            ),
            ClusterLocationInfo(
                cluster_index=(1, 0), global_location_index=2, cluster_location_index=0
            ),
            ClusterLocationInfo(
                cluster_index=(1, 0), global_location_index=3, cluster_location_index=1
            ),
        ]
    )
