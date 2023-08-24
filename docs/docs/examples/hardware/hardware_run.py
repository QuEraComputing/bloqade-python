import sys
import os
sys.path.insert(0, os.path.abspath('..'))
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from MIS import MIS_ansatz, MIS_problem, optimization, graph
import boto3
import os
import configparser
import pickle


if __name__ == "__main__":

    print("Loading credentials!")

    # # Create a config parser
    config = configparser.ConfigParser()

    # # Read the AWS credentials file
    config.read(os.path.expanduser("~/.aws/credentials"))

    # # Get the access keys
    aws_access_key_id = config.get('716981252513_QC_App_Algo_RD', 'aws_access_key_id')
    aws_secret_access_key = config.get('716981252513_QC_App_Algo_RD', 'aws_secret_access_key')

    os.environ['AWS_ACCESS_KEY_ID'] = aws_access_key_id
    os.environ['AWS_SECRET_ACCESS_KEY'] = aws_secret_access_key

    print("Credentials successfully loaded!")
    
    # Create the graph
    pos, G = graph.kings_graph(11, 11, 0.7, seed = 4)
    # Save the data to a pickle file
    with open('graph.pkl', 'wb') as f:
        pickle.dump((pos, G), f)

    # Compute unitdisk radius
    unitdisk_radius, min_radius, max_radius = graph.find_UDG_radius(pos, G)

    # Set up the problem
    problem = MIS_problem.MIS_problem(graph=G, positions=pos,
                                      post_process=False,
                                      penalty_factor=1E3)
    
    ansatz = MIS_ansatz.MIS_ansatz(problem=problem, backend="quantum_braket",
                                    num_shots=30, blockade_radius=8, 
                                    unitdisk_radius=unitdisk_radius, 
                                    num_time_points=3,
                                    ansatz_type="linear")

    # Initial paramters 
    x0 = np.array([0.25, 1, 0.25] + [-10, -10, 10, 20])

    print("Starting the optimization!")
    problem.cost_function(ansatz=ansatz, x=x0)
    
    opt = optimization.Optimizer(problem=problem, ansatz=ansatz, 
                                 x_init=x0,  max_iter=30,
                                 save_progress=True,
                                 method="COBYLA")
    res = opt.optimize()        

    print("Successfully finished!")

 




