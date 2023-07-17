from bloqade import piecewise_linear, start
from bloqade.ir.location import Square
import numpy as np
from scipy.optimize import minimize
from bloqade.builder.optimizer import Optimization
from pathos.multiprocessing import Pool, cpu_count
import datetime
import json
import sys

# Initilize the program
durations = [0.3, 1.6, 0.3]

mis_udg_program = (
    Square(3, 5)
    .apply_defect_density(0.5)
    .rydberg.rabi
    .amplitude.uniform.piecewise_linear(durations, ["amplitude_" + str(i+1) for i in range(len(durations)+1)])
    .detuning.uniform.piecewise_linear(durations, ["detuning_" + str(i+1) for i in range(len(durations)+1)])
)

# Define the cost function for the variatioal parameter optimization
def cost_function(num_shots, x):

    # Define the bounds
    bounds_amplitude = [(0, 25)] * 4
    bounds_detuning = [(-125, 125)] * 4

    # Apply the transformation to map x to the bounded interval
    amplitude_values = [lower + (upper - lower) / (1 + np.exp(-xi)) for xi, (lower, upper) in zip(x[:len(x)//2], bounds_amplitude)]
    detuning_values = [lower + (upper - lower) / (1 + np.exp(-xi)) for xi, (lower, upper) in zip(x[len(x)//2:], bounds_detuning)]

    kwargs_amplitude = {"amplitude_" + str(i+1): amplitude_values[i] for i in range(len(x)//2)}
    kwargs_detuning = {"detuning_" + str(i+1): detuning_values[i] for i in range(len(x)//2)}
    kwargs = {**kwargs_amplitude, **kwargs_detuning}
    
    mis_udg_job = mis_udg_program.assign(**kwargs)
    hw_job = mis_udg_job.braket_local_simulator(num_shots).submit()
    
    post_bitstrings = np.array(hw_job.report().bitstrings[0])
    
    # Return the cost
    return -(1-post_bitstrings).sum(axis=1).mean()


def run_optimization(opt, x0, i, maxiter):
    print(f"Current run: {i}\t")
    np.random.seed(i)
    opt.optimize(x0=x0, maxiter=maxiter)
    return opt.get_cost_history(), opt.get_res()


if __name__ == "__main__":

    # Read simulation parameters from terminal
    opt_name = str(sys.argv[1])
    seed = int(sys.argv[2])
    num_shots = int(sys.argv[3])
    num_repeats = 10

    # Initialize the optimization class
    opt = Optimization(callback_step=20, cost_function=lambda x: cost_function(num_shots, x), method=opt_name)
    np.random.seed(seed)
    x0 = np.random.rand(2 * 4)

    # Run in parallel
    with Pool(cpu_count()) as p:
        results = p.starmap(run_optimization, [(opt, x0, i, num_shots) for i in range(num_repeats)])

    # Generate a timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Save the results to a json file
    with open(f'results_seed_{seed}_shots_{num_shots}_{timestamp}.json', 'w') as f:
        json.dump(results, f)

