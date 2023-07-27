from scipy.optimize import minimize
import time
import json 
import os


class Optimizer:

    def __init__(self, problem, ansatz, x_init, max_iter, save_progress=False):
        
        self.problem = problem
        self.ansatz = ansatz
        self.x_init = x_init
        self.max_iter = max_iter
        self.bitstring_history = []
        self.parameter_history = []
        self.cost_history = []
        self.old_json_path = None
        self.save_progress = save_progress  
    
    def _array_cache(self, func):
        # Cache results such that evaluation with the same parameters is avoided
        cache = {}
        def wrapper(x, *args, **kwargs):
            x_tuple = tuple(x)
            if x_tuple in cache:
                return cache[x_tuple]
            result = func(x, *args, **kwargs)
            cache[x_tuple] = result
            return result
        return wrapper


    def _tracking_cost_function(self, x):
        
        cost, bitstrings = self.problem.cost_function(self.ansatz, x)
        print(f"Cost value is {cost}")

        self.bitstring_history.append(bitstrings.tolist())
        self.parameter_history.append(x.tolist())
        self.cost_history.append(cost)

        # Save progress to JSON if the flag is set
        if self.save_progress:
            self._save_progress_to_json()

        return cost

    def _save_progress_to_json(self):
        # Define the path of the new JSON file
        timestamp = time.strftime("%Y%m%d-%H%M%S")  # Current time as a string
        new_json_path = f"progress_{timestamp}.json"

        # Save the progress to the new JSON file
        progress = {
            "bitstring_history": self.bitstring_history,
            "parameter_history": self.parameter_history,
            "cost_history": self.cost_history
        }
        with open(new_json_path, "w") as f:
            json.dump(progress, f)

        # If the old file exists, delete it
        if self.old_json_path and os.path.exists(self.old_json_path):
            os.remove(self.old_json_path)

        # Update the path of the old JSON file
        self.old_json_path = new_json_path

    def optimize(self, method='COBYLA'):
        result = minimize(self._array_cache(self._tracking_cost_function), self.x_init, method=method, options={"maxiter": self.max_iter})
        return result