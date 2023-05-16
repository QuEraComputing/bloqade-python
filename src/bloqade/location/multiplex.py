from .base import AtomArrangement
from .list import ListOfLocations
from decimal import Decimal
from pydantic import BaseModel, validator, ValidationError

from bloqade.submission.capabilities import get_capabilities

from typing import List, Tuple, Union

from quera_ahs_utils.quera_ir.task_results import QuEraShotResult, QuEraTaskResults


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


class MultiplexDecoder(BaseModel):
    mapping: List[SiteClusterInfo]

    # should work if we go to the coordinate-based indexing system
    @validator("mapping")
    def sites_belong_to_unqiue_cluster(cls, mapping):
        sites = [ele.global_site_index for ele in mapping]
        unique_sites = set(sites)
        if len(sites) != len(unique_sites):
            raise ValidationError("one or more sites mapped to multiple clusters")

        return mapping

    @property
    def sites_per_cluster(self):
        local_site_indices = set()

        for site in self.mapping:
            local_site_indices.add(site.local_site_index)

        return len(local_site_indices)

    # map individual atom indices (in the context of the ENTIRE geometry)
    # to the cluster-specific indices:
    # {}
    def get_site_indices(self):
        site_indices = {}
        for site_cluster in self.mapping:  # iterate through global_site_index
            global_site_index = site_cluster.global_site_index
            local_site_index = site_cluster.local_site_index
            site_indices[global_site_index] = local_site_index

        return site_indices

    # should work if we go to coordinate-based indexing
    # map each cluster index to the global index
    def get_cluster_indices(self):
        site_indices = self.get_site_indices()

        cluster_indices = {}
        for site_cluster in self.mapping:
            global_site_index = site_cluster.global_site_index
            cluster_index = site_cluster.cluster_index

            cluster_indices[cluster_index] = cluster_indices.get(cluster_index, []) + [
                global_site_index
            ]

        return {
            cluster_index: sorted(sites, key=lambda site: site_indices[site])
            for cluster_index, sites in cluster_indices.items()
        }

    def demultiplex_results(
        self, task_result: QuEraTaskResults, clusters: Union[int, List[int]] = []
    ) -> QuEraTaskResults:
        cluster_indices = self.get_cluster_indices()

        shot_outputs = []

        match clusters:
            case int(cluster_index):
                clusters = [cluster_index]
            case list() if clusters:
                pass
            case _:
                clusters = cluster_indices.keys()

        for full_shot_result in task_result.shot_outputs:
            for cluster_site_indices in cluster_indices.values():
                shot_outputs.append(
                    QuEraShotResult(
                        shot_status=full_shot_result.shot_status,
                        pre_sequence=[
                            full_shot_result.pre_sequence[index]
                            for index in cluster_site_indices
                        ],
                        post_sequence=[
                            full_shot_result.post_sequence[index]
                            for index in cluster_site_indices
                        ],
                    )
                )

        return QuEraTaskResults(
            task_status=task_result.task_status, shot_outputs=shot_outputs
        )


def multiplex_register(
    register_ast: AtomArrangement, cluster_spacing, capabilities=None
) -> Tuple[ListOfLocations, List[SiteClusterInfo]]:
    if capabilities is None:
        capabilities = get_capabilities()

    height_max = Decimal(capabilities.capabilities.lattice.area.height) / Decimal(1e-6)
    width_max = Decimal(capabilities.capabilities.lattice.area.width) / Decimal(1e-6)
    number_sites_max = capabilities.capabilities.lattice.geometry.number_sites_max

    register_sites = list(register_ast.enumerate())
    # get minimum and maximum x,y coords for existing problem spacing
    x_min = x_max = 0
    y_min = y_max = 0
    for site in register_sites:
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
        if global_site_index + len(register_sites) > number_sites_max:
            break
        # reached the maximum number of batches possible along x-direction
        if y_shift + single_problem_height > height_max:
            break

        cluster_index_x = 0
        while True:
            x_shift = cluster_index_x * Decimal(single_problem_width + cluster_spacing)
            # reached the maximum number of batches possible given n_site_max
            if global_site_index + len(register_sites) > number_sites_max:
                break
            # reached the maximum number of batches possible along x-direction
            if x_shift + single_problem_width > width_max:
                cluster_index_y += 1
                break

            for local_site_index, (x_coord, y_coord) in enumerate(register_sites):
                sites.append((x_coord + float(x_shift), y_coord + float(y_shift)))
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

    return ListOfLocations(sites), MultiplexDecoder(mapping=mapping)
