from pydantic import BaseModel, validator, ValidationError

from typing import List, Tuple, Union

from bloqade.submission.ir.task_results import (
    QuEraShotResult,
    QuEraTaskResults,
)


class ClusterLocationInfo(BaseModel):
    """Class that stores the mapping of batched jobs.

    Args:
        cluster_index (int): the index of the cluster a site belongs to
        global_location_index (int): the index of the site in the multplexed system
        cluster_location_index (int): the index of the site in the original system
    """

    cluster_index: Tuple[int, int]
    global_location_index: int
    cluster_location_index: int


class ParallelDecoder(BaseModel):
    mapping: List[ClusterLocationInfo]
    locations_per_cluster: int
    number_of_cluster: int

    class Config:
        frozen = True

    def __init__(self, mapping: List[ClusterLocationInfo]):
        cluster_location_indices = set()
        cluster_indices = set()

        for site in mapping:
            cluster_location_indices.add(site.cluster_location_index)
            cluster_indices.add(site.cluster_index)

        super().__init__(
            mapping=mapping,
            locations_per_cluster=len(cluster_location_indices),
            number_of_cluster=len(cluster_indices),
        )

    # should work if we go to the coordinate-based indexing system
    @validator("mapping")
    def sites_belong_to_unqiue_cluster(cls, mapping):
        sites = [ele.global_location_index for ele in mapping]
        unique_sites = set(sites)
        if len(sites) != len(unique_sites):
            raise ValidationError("one or more sites mapped to multiple clusters")

        cluster_indices = {}
        for location_cluster_info in mapping:
            cluster_index = location_cluster_info.cluster_index
            global_site_index = location_cluster_info.global_location_index
            cluster_indices.setdefault(cluster_index, set([])).add(global_site_index)

        for cluster_index, location_indices in cluster_indices.items():
            for other_cluster_index, other_location_indices in cluster_indices.items():
                if cluster_index == other_cluster_index:
                    continue
                if location_indices.intersection(other_location_indices):
                    raise ValidationError(
                        "one or more sites mapped to multiple clusters"
                    )

        return mapping

    # map individual atom indices (in the context of the ENTIRE geometry)
    # to the cluster-specific indices:
    # {}
    def get_location_indices(self):
        site_indices = {}
        for location_cluster_info in self.mapping:  # iterate through global_site_index
            global_site_index = location_cluster_info.global_location_index
            local_site_index = location_cluster_info.cluster_location_index
            site_indices[global_site_index] = local_site_index

        return site_indices

    # should work if we go to coordinate-based indexing
    # map each cluster index to the global index
    def get_cluster_indices(self):
        site_indices = self.get_location_indices()

        cluster_indices = {}
        for location_cluster_info in self.mapping:
            global_site_index = location_cluster_info.global_location_index
            cluster_index = location_cluster_info.cluster_index

            cluster_indices[cluster_index] = cluster_indices.get(cluster_index, []) + [
                global_site_index
            ]

        return {
            cluster_index: sorted(sites, key=lambda site: site_indices[site])
            for cluster_index, sites in cluster_indices.items()
        }

    def decode_results(
        self,
        task_result: QuEraTaskResults,
        clusters: Union[Tuple[int, int], List[Tuple[int, int]]] = [],
    ) -> QuEraTaskResults:
        cluster_indices = self.get_cluster_indices()

        shot_outputs = []

        match clusters:
            case tuple() as cluster_index:
                clusters = [cluster_index]
            case list() if clusters:
                pass
            case _:
                clusters = cluster_indices.keys()

        for full_shot_result in task_result.shot_outputs:
            for cluster_index in clusters:
                global_indices = cluster_indices.get(cluster_index, [])
                if global_indices:
                    shot_outputs.append(
                        QuEraShotResult(
                            shot_status=full_shot_result.shot_status,
                            pre_sequence=[
                                full_shot_result.pre_sequence[index]
                                for index in global_indices
                            ],
                            post_sequence=[
                                full_shot_result.post_sequence[index]
                                for index in global_indices
                            ],
                        )
                    )

        return QuEraTaskResults(
            task_status=task_result.task_status, shot_outputs=shot_outputs
        )
