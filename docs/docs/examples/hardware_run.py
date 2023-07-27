
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from MIS import MIS_ansatz, MIS_problem, optimization, graph
import boto3


def send_sns_notification():
    sns = boto3.client('sns')
    response = sns.publish(
        TopicArn='your-topic-arn',    
        Message='The optimization task has completed successfully.',
        Subject='Notification from EC2 instance',
    )

def shutdown(instance_id):
    # Then, shut down the EC2 instance
    ec2 = boto3.client('ec2', region_name='us-east-1')
    ec2.stop_instances(InstanceIds=[instance_id])


if __name__ == "__main__":

    pos, small_G = graph.kings_graph(10, 10, 0.5, seed = 1)
    unitdisk_radius, min_radius, max_radius = graph.find_UDG_radius(pos, small_G)

    # Plot and save the graph
    # fig, ax = plt.subplots()
    # nx.draw(small_G, pos, with_labels=True, ax=ax)
    # node_of_interest = 3
    # circle = patches.Circle(pos[node_of_interest], unitdisk_radius,
    #                        fill=False, linewidth=2, linestyle='--')  # create a circle patch
    # ax.add_patch(circle)  # add the circle patch to the axes

    # Set up the problem
    problem = MIS_problem.MIS_problem(graph=small_G, positions=pos)
    num_time_points = 3
    ansatz = MIS_ansatz.MIS_ansatz(problem=problem, q_hardware=True,
                                    num_shots=30, lattice_spacing=8, 
                                    unitdisk_radius=unitdisk_radius, 
                                    num_time_points=num_time_points,
                                    max_iter=30)

    # Initial paramters 
    x0 = np.array([0.25, 1, 0.25] + [-10, -10, 10, 20])
    opt = optimization.Optimizer(problem=problem, ansatz=ansatz, 
                                 x_init=x0, save_progress=True)
    res = opt.optimize()    

    # TODO: Add rest of plotting


    # Shut down EC2 instance and send email notification
    # shutdown(instance_id='i-02f8727d3a2f56772')




