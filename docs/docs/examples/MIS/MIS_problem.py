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
        
        in_range, transformed_x, penalty = ansatz.parameter_transform(x)

        # The QPU is only called if the parameters are within bounds
        if in_range:
            bitstrings = ansatz.get_bitstrings(transformed_x)
        else:
            bitstrings = self.current_bitstring

        if self.post_process == True:
            post_processed_bitstrings = ansatz.post_process_MIS(bitstrings)
        elif self.post_process == False: 
            post_processed_bitstrings = bitstrings

        cost = -(1-post_processed_bitstrings).sum(axis=1).mean()
        self.current_bitstring = post_processed_bitstrings
        self.current_cost = cost
        return cost + self.penalty_factor * penalty