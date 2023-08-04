from scipy.optimize import minimize
import time
import json 
import os
import numpy as np

class Optimizer:

    def __init__(self, method, problem, ansatz, x_init, max_iter, save_progress=False):
        
        self.method = method
        self.problem = problem
        self.ansatz = ansatz
        self.x_init = x_init
        self.max_iter = max_iter
        self.parameter_history = []
        self.cost_history = []
        self.bitstring_history = []
        self.old_json_path = None
        self.save_progress = save_progress  
        self.result = None
    
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
        
        cost = self.problem.cost_function(self.ansatz, x)
        print(f"Cost value is {cost}")

        self.parameter_history.append(x.tolist())
        self.cost_history.append(self.problem.current_cost)
        self.bitstring_history.append(self.problem.current_bitstring.tolist())

        # Save progress to JSON if the flag is set
        if self.save_progress:
            self._save_progress_to_json()
        return cost

    def _save_progress_to_json(self):

        # Define the path of the new JSON file
        backend = self.ansatz._backend_info["backend"]
        timestamp = time.strftime("%Y%m%d-%H%M%S")  # Current time as a string
        new_json_path = f"optimizer_{backend}_progress_{timestamp}.json"

        # Save the progress to the new JSON file

        # TODO: Get rid of bitstring history, & put into ansatz for get_bitstring()

        progress = {
            "parameter_history": self.parameter_history,
            "cost_history": self.cost_history,
            "bitstring_history" : self.bitstring_history
        }
        with open(new_json_path, "w") as f:
            json.dump(progress, f)

        # If the old file exists, delete it
        if self.old_json_path and os.path.exists(self.old_json_path):
            os.remove(self.old_json_path)

        # Update the path of the old JSON file
        self.old_json_path = new_json_path


    def _spsa(self, delta, learning_rate):
        
        # Initialize variables
        N = len(self.x_init)
        x = self.x_init.copy()
  
        for _ in range(self.max_iter):

            rand_vec = 2 * np.random.binomial(1, 0.5, N) - 1
            x_plus = x +  delta * rand_vec
            x_minus = x - delta * rand_vec

            y_plus = self._array_cache(self._tracking_cost_function)(x_plus)
            # self.problem.cost_function(self.ansatz, x_plus)
            y_minus = self._array_cache(self._tracking_cost_function)(x_minus)
            # self.problem.cost_function(self.ansatz, x_minus)

            g_hat = (y_plus - y_minus) / (2.0 * delta * rand_vec)
            x -= learning_rate * g_hat

        # Generate the same output as scipy.optimize.minimize
        return {'fun': self._tracking_cost_function(x), 'x': x, 'success': True, 'message': '', 'nit': self.max_iter}


    def optimize(self, delta=0.01, learning_rate=0.005):
        if self.method == 'SPSA':
            result = self._spsa(delta, learning_rate)
        else:
            result = minimize(self._array_cache(self._tracking_cost_function), self.x_init, method=self.method, options={"maxiter": self.max_iter})
        self.result = result
        return result


    