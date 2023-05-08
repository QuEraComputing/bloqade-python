import quera_ahs_utils.quera_ir.task_specification as task_spec


class LatticeCodeGen:
    def __init__(self, assignments) -> None:
        self.assignments = assignments

    def emit(self, lattice):
        sites = []
        filling = []
        for site in lattice.enumerate():
            sites.append(tuple(site))
            filling.append(1)

        return task_spec.Lattice(sites=sites, filling=filling)
