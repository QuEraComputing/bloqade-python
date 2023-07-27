from bloqade import piecewise_linear, start
from bloqade.ir.location import Square
import numpy as np
from scipy.optimize import minimize
from bloqade.builder.optimizer import Optimization
from bloqade.submission.capabilities import get_capabilities
import matplotlib.pyplot as plt
import networkx as nx
import datetime
import json
import warnings
warnings.filterwarnings('ignore')


def parameter_transform(duration_values, detuning_values):

    # Transform parameter values to correct range
    duration_values = np.abs(duration_values)
    duration_values = (duration_values / np.sum(duration_values)) * total_time 
    detuning_values = det_min + (det_max - det_min) / (1 + np.exp(-detuning_values))

    return duration_values, detuning_values

def are_neighbors(pos1, pos2):
    
    dx = abs(float(pos1[0].value) - float(pos2[0].value))
    dy = abs(float(pos1[1].value) - float(pos2[1].value))

    return dx <= 5 and dy <= 5 and (dx + dy) > 0

def generate_and_plot_graph(mis_udg_program, bitstring=None, mis=False):

    # Create a new graph
    G = nx.Graph()
    locations = mis_udg_program.program.register.location_list

    # Maintain an ordered list of nodes
    nodes = []

    # Create dictionaries for colors and positions
    colors = {}
    pos = {}

    # If bitstring is not provided, create a bitstring with all ones
    if bitstring is None:
        bitstring = np.ones(len(locations))

    # Add nodes for all locations
    for loc, bit in zip(locations, bitstring):
        node = (int(loc.position[0].value), int(loc.position[1].value))
        nodes.append(node)
        G.add_node(node)

        # Set the node color and position based on the filling
        if loc.filling.value == 1:
            colors[node] = 'red' if bit == 0 else 'black'
        else:
            colors[node] = 'gray'
        pos[node] = node

    # Add edges for neighboring filled locations
    filled_locations = [loc for loc in locations if loc.filling.value == 1]
    for loc1 in filled_locations:
        for loc2 in filled_locations:
            if loc1 != loc2 and are_neighbors(loc1.position, loc2.position):
                G.add_edge((int(loc1.position[0].value), int(loc1.position[1].value)), 
                            (int(loc2.position[0].value), int(loc2.position[1].value)))

    # If MIS should be computed and displayed, compute it
    if mis:
        filled_nodes = [node for node, color in colors.items() if color != 'gray']
        G_filled = G.subgraph(filled_nodes)
        mis_set = nx.maximal_independent_set(G_filled)
        for node in mis_set:
            colors[node] = 'red'

    # Get the color list in the same order as the nodes
    color_list = [colors[node] for node in G.nodes]

    # Draw the graph
    nx.draw(G, pos, node_color=color_list, with_labels=False)
    plt.show()

    return nodes, G


def get_bitstrings(duration_values, detuning_values, q_hardware=False):

    # Assign parameters for MIS program
    kwargs_duration = {"duration_" + str(i+1): val for i, val in enumerate(duration_values)}
    kwargs_detuning = {"detuning_" + str(i+1): val for i, val in enumerate(detuning_values)}
    kwargs = {**kwargs_duration, **kwargs_detuning}
    mis_udg_job = mis_udg_program.assign(**kwargs)

    # Run on hardware or local simulator 
    if q_hardware == True:
        hw_job = mis_udg_job.braket(num_shots).submit()
    else:
        hw_job = mis_udg_job.braket_local_simulator(num_shots).submit()

    # TODO: Add some storage of the bitstrings 

    # Perhaps the best solution would be if we get a task id back 
    # which we can store and use later to get the result back 


    return np.array(hw_job.report().bitstrings[0])

def post_process_MIS(bitstrings):

    post_processed_bitstrings = []

    for bitstring in bitstrings:

        inds = np.nonzero(bitstring==0)[0]    # Find indices of IS vertices

        # TODO: this should also check if the site is even occupied or not 

        nodes_to_check = [nodes[i] for i in inds]  # Map indices to nodes
        subgraph = nx.subgraph(G, nodes_to_check)  # Generate a subgraph from those vertices.
        inds2 = nx.maximal_independent_set(subgraph, seed=0)
        post_processed_bitstring = np.array([0 if node in inds2 else 1 for node in nodes])

        post_processed_bitstrings.append(post_processed_bitstring)

    if len(post_processed_bitstrings) == 0: 
        raise ValueError("no independent sets found! increase number of shots.")

    return np.asarray(post_processed_bitstrings)

def avg_MIS_size(bitstrings):
    return (1-bitstrings).sum(axis=1).mean()

def cost_function(x, q_hardware=False):
    
    duration_values = x[0:num_time_points]
    detuning_values = x[num_time_points:]

    duration_values, detuning_values = parameter_transform(duration_values, detuning_values)
    bitstrings = get_bitstrings(duration_values, detuning_values, q_hardware)
    post_processed_bitstrings = post_process_MIS(bitstrings)

    # It is not clear to me how tracking of the bitstrings can be done within 
    # the Optimization class since the cost function will only ever return a scalar

    # It could perhaps optionally return the bitstrings which are then picked up by the
    # Optimizer class and stored 
    
    return -avg_MIS_size(post_processed_bitstrings)

if __name__ == "__main__":

    # Probably some environment settings for harware runs

    # Get parameter bounds 
    capabilities = get_capabilities()

    det_max = capabilities.capabilities.rydberg.global_.detuning_max / 1E6
    det_min = capabilities.capabilities.rydberg.global_.detuning_min / 1E6

    amp_min = capabilities.capabilities.rydberg.global_.rabi_frequency_min / 1E6
    amp_max = capabilities.capabilities.rydberg.global_.rabi_frequency_max / 1E6

    total_time = capabilities.capabilities.rydberg.global_.time_max * 1E6

    # Set hyperparameters
    num_shots = 50
    num_time_points = 3

    # Initialize MIS program 
    mis_udg_program = (
        Square(3, 5)
        .apply_defect_density(0.4, np.random.default_rng(10))
        .rydberg.rabi
        .amplitude.uniform.piecewise_linear(["duration_" + str(i+1) for i in range(num_time_points)], [0.] + [amp_max] * (num_time_points-1)  + [0.])
        .detuning.uniform.piecewise_linear(["duration_" + str(i+1) for i in range(num_time_points)], ["detuning_" + str(i+1) for i in range(num_time_points+1)])
    )

    # FIXME: This is blocking until the figure is closed 
    nodes, G = generate_and_plot_graph(mis_udg_program)

    # Initialize the parameters and optimizer
    x0 = 2 * np.random.rand(2*num_time_points+1) - 1
    opt_cobyla = Optimization(callback_step=1, cost_function=cost_function, method="COBYLA")

    # Run the optimization
    opt_cobyla.optimize(x0=x0, maxiter=50)

    res = opt_cobyla.get_res()
    cost_history = opt_cobyla.get_cost_history()
    parameter_history = opt_cobyla.get_parameter_history()

    # Generate a timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


    # Save the results to a json file
    #with open(f'test_run_{timestamp}.json', 'w') as f:
    #    json.dump({"res": res, "cost_history": cost_history, "parameter_history": parameter_history}, f)

