from scipy.optimize import minimize
from typing import Callable, Optional, List, Dict, Union, Tuple
import numpy as np
import copy 


def array_cache(func):
    cache = {}

    def wrapper(x, *args, **kwargs):
        x_tuple = tuple(x)
        if x_tuple in cache:
            return cache[x_tuple]
        result = func(x, *args, **kwargs)
        cache[x_tuple] = result
        return result

    return wrapper


class Optimization:

    def __init__(self, callback_step: int, cost_function: Callable, method: str):
        self.__cost_history = []
        # self.__cost_function = cost_function
        self.__iter = 0
        self.__res = None
        self.__callback_step = callback_step
        self.__method = method
        self.__nev = 0
        self.__cost_function = array_cache(cost_function)


    def __callback(self, x: np.ndarray) -> None:
        feval = self.__cost_function(x)
        self.__iter += 1
        if self.__iter % self.__callback_step == 0:
            print(f"Cost function value: {feval}")
        self.__cost_history.append(feval)

    def optimize(self, x0: np.ndarray, maxiter: int, constraints: Optional[List[Dict]] = None, bounds: Optional[List[Tuple[float, float]]] = None) -> None:
        
        self.__cost_history = []
        self.__iter = 0
        # self.__callback(x0)

        if self.__method == "SPSA":
            self.__res = self.__spsa_optimizer(self.__cost_function, x0, maxiter, callback=self.__callback)
        else:
            self.__res = minimize(self.__cost_function, x0, method=self.__method, callback=self.__callback, options={"maxiter": maxiter}, constraints=constraints, bounds=bounds)
    
    def get_cost_history(self) -> List[float]:
        return self.__cost_history
    
    def get_res(self) -> Dict[str, Union[np.ndarray, str, bool]]:
        return self.__res
    
    def __spsa_optimizer(self, cost_function: Callable, x0: np.ndarray, maxiter: int, callback: Callable, alpha=0.602, gamma=0.101) -> Dict[str, Union[np.ndarray, str, bool]]:
        x = copy.deepcopy(x0)

        self.__nev = 0

        for _ in range(maxiter):
            # Calculate the perturbation
            delta = np.random.choice([-1, 1], size=len(x))

            # Evaluate the cost function at the positive and negative perturbed points
            cost_plus = cost_function(x + alpha * delta)
            cost_minus = cost_function(x - alpha * delta)

            #cost_plusl.get()
            #cost_minus.get()

            # Estimate the gradient
            gradient = (cost_plus - cost_minus) / (2 * alpha * delta)

            # Update the parameters
            x -= gamma * gradient

            # Call the callback function at each iteration
            #callback(x)
            self.__cost_history.append(cost_function(x))
            self.__nev += 2

        return {
            'x': x,
            'nfev': self.__nev,
            'success': True,
            'status': 'Finished iterations',
            'message': "Optimization terminated successfully.",
        }
