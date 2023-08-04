from .problem import Problem

class MIS_problem(Problem):
    
    def __init__(self, graph, positions, penalty_factor, post_process) -> None:
        self.graph = graph
        self.positions = positions
        self.penalty_factor = penalty_factor
        self.post_process = post_process
        self.current_bitstring = None
        self.current_cost = None

    def cost_function(self, ansatz, x):
        
        duration_values = x[:ansatz.num_time_points]
        detuning_values = x[ansatz.num_time_points:]

        duration_values, detuning_values, penalty = ansatz.parameter_transform(duration_values, detuning_values)

        bitstrings = ansatz.get_bitstrings(list(duration_values)+list(detuning_values))

        if self.post_process == True:
            post_processed_bitstrings = ansatz.post_process_MIS(bitstrings)
        elif self.post_process == False: 
            post_processed_bitstrings = bitstrings

        cost = -(1-post_processed_bitstrings).sum(axis=1).mean()
        self.current_bitstring = post_processed_bitstrings
        self.current_cost = cost
        return cost + self.penalty_factor * penalty