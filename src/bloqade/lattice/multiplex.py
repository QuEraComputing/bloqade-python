from .base import Lattice
from .list import ListOfPositions
from decimal import Decimal
from pydantic import BaseModel

from bloqade.task import Program
from bloqade.hardware.capabilities import Capabilities

from typing import List, Tuple


class SiteClusterInfo(BaseModel):
    """Class that stores the mapping of batched jobs.

    Args:
        cluster_index (int): the index of the cluster a site belongs to
        global_site_index (int): the index of the site in the multplexed system
        local_site_index (int): the index of the site in the original system
    """

    cluster_index: tuple[int, int]
    global_site_index: int
    local_site_index: int


def multiplex_lattice(
    lattice_ast: Lattice, capabilities, cluster_spacing
) -> Tuple[ListOfPositions, List[SiteClusterInfo]]:
    lattice_sites = list(lattice_ast.enumerate())
    print(lattice_sites)
    # get minimum and maximum x,y coords for existing problem spacing
    x_min = x_max = 0
    y_min = y_max = 0
    for site in lattice_sites:
        if site[0] < x_min:
            x_min = site[0]
        elif site[0] > x_max:
            x_max = site[0]

        if site[1] < y_min:
            y_min = site[1]
        elif site[1] > y_max:
            y_max = site[1]

    cluster_spacing = Decimal(cluster_spacing)
    single_problem_width = Decimal(
        (x_max - x_min).item()
    )  # conversion from np.int64 to Decimal not supported
    single_problem_height = Decimal((y_max - y_min).item())

    cluster_index_x = 0
    cluster_index_y = 0
    global_site_index = 0

    sites = []
    mapping = []
    while True:
        y_shift = cluster_index_y * Decimal(single_problem_height + cluster_spacing)
        # reached the maximum number of batches possible given n_site_max
        if global_site_index + len(lattice_sites) > capabilities.num_sites_max:
            break
        # reached the maximum number of batches possible along x-direction
        if y_shift + single_problem_height > capabilities.max_height:
            break

        cluster_index_x = 0
        while True:
            x_shift = cluster_index_x * Decimal(single_problem_width + cluster_spacing)
            # reached the maximum number of batches possible given n_site_max
            if global_site_index + len(lattice_sites) > capabilities.num_sites_max:
                break
            # reached the maximum number of batches possible along x-direction
            if x_shift + single_problem_width > capabilities.max_width:
                cluster_index_y += 1
                break

            for local_site_index, (x_coord, y_coord) in enumerate(lattice_sites):
                sites.append((x_coord + x_shift, y_coord + y_shift))
                mapping.append(
                    SiteClusterInfo(
                        cluster_index=(
                            cluster_index_x,
                            cluster_index_y,
                        ),
                        global_site_index=global_site_index,
                        local_site_index=local_site_index,
                    )
                )

                global_site_index += 1

            cluster_index_x += 1

    return ListOfPositions(sites), mapping


# create a new program with multiplexed geometry and mapping provided
def multiplex_program(
    prog: "Program", capabilities: Capabilities, cluster_spacing: float
) -> "Program":
    multiplexed_lattice, mapping = multiplex_lattice(
        prog.lattice, capabilities, cluster_spacing
    )
    multiplexed_prog = Program(multiplexed_lattice, prog.seq, prog.assignments)
    multiplexed_prog.mapping = mapping
    return multiplexed_prog
