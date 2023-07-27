from .problem import Problem

class MIS_problem(Problem):
    
    def __init__(self, graph, positions) -> None:
        self.graph = graph
        self.positions = positions

    def cost_function(self, ansatz, x):
        
        duration_values = x[:ansatz.num_time_points]
        detuning_values = x[ansatz.num_time_points:]

        duration_values, detuning_values, penalty = ansatz.parameter_transform(duration_values, detuning_values)
        # post_processed_bitstrings = ansatz.get_solutions(duration_values+detuning_values)
        post_processed_bitstrings = ansatz.get_bitstrings(duration_values+detuning_values)

        return -(1-post_processed_bitstrings).sum(axis=1).mean() + 100 * penalty, post_processed_bitstrings