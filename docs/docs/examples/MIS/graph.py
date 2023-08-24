import networkx as nx
import random
import numpy as np

def generate_grid_graph(n, drop_rate):
    # Create a complete grid graph
    G = nx.grid_2d_graph(n, n)
    
    # Create a dictionary for node positions
    pos = {node: node for node in G.nodes()}
    
    # Randomly drop nodes
    for node in list(G.nodes):
        if random.random() < drop_rate:
            G.remove_node(node)
            
    return G, pos


def find_UDG_radius(position, graph):
    
    dists = np.sqrt((position[:,0,None] - position[:,0])**2
               + (position[:,1,None] - position[:,1])**2)
    rmin = 0
    rmax = np.inf
    for i in range(position.shape[0]):
        for j in range(i+1,position.shape[0]):
            if (i,j) in graph.edges:
                if rmin<dists[i,j]:
                    rmin = dists[i,j]
            elif (i,j) not in graph.edges:
                if rmax>dists[i,j]:
                    rmax = dists[i,j]
    
    if rmin>rmax:
        print(rmin,rmax)
        raise BaseException("Graph is not a unit disk graph!")
    
    return np.sqrt(rmin*rmax),rmin,rmax

def kings_graph(numx,numy,filling=0.7,seed=None):

    xx,yy = np.meshgrid(range(numx),range(numy))
    num_points = int(numx*numy*filling)
    rand = np.random.default_rng(seed=seed)
    # Generate points
    points = np.array([xx.flatten(),yy.flatten()]).T
    points = points[rand.permutation(numx*numy)[0:num_points],:]
    # Generate a unit disk graph by thresholding distances between points.
    distances = np.sqrt((points[:,0] - points[:,0,None])**2 + (points[:,1] - points[:,1,None])**2)
    graph     = nx.Graph(distances<np.sqrt(2)+1E-10)
    
    graph.remove_edges_from(nx.selfloop_edges(graph))
    return points, graph
