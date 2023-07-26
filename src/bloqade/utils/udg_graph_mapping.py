# -*- coding: utf-8 -*-
"""
Created on Wed Jul 26 12:04:58 2023

@author: jwurtz
"""
import numpy as np
import networkx as nx

def find_UDG_radius(position, graph):
    '''
    Computes the optimal unit disk radius for a particular set of positions and graph.
    position   - [N x 2] array of points
    graph       - network connectivity graph. This should be a unit disk graph.
    
    returns
    radius      - Optimal unit disk radius of the graph
    rmin        - Minimum distance
    rmax        - Maximum distance
    '''
    
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



def __row_cluster(points0:np.ndarray, threshold:float,plotit = False):
    """
    Clusters points in 1 dimension using tree clustering
    points0 - Initial points
    threshold - The minimum distance between clusters
    """
    
    assert len(points0.shape)==1,"Data must be 1 dimensional"
    assert np.isreal(points0).all(),"Data must be real"
    
    
    points = np.copy(points0)
    weights= np.ones(len(points))
    generation = np.zeros(len(points))
    
    
    i = 0
    for ctr in range(len(points0)-1):
        dists = abs(points.reshape(len(points),1) - points.reshape(1,len(points)))
        dists[range(len(points)),range(len(points))] = np.inf
        
        if dists.min()>=threshold:
            break
        
        i += dists.min()
        
        mindist = np.unravel_index(np.argmin(dists),dists.shape)
        points[[mindist[0],mindist[1]]]
        
        newpt = (points[mindist[0]] * weights[mindist[0]] + \
                 points[mindist[1]] * weights[mindist[1]])/ \
                (weights[mindist[0]] + weights[mindist[1]])
        newwt = weights[mindist[0]] + weights[mindist[1]]
        
        points = np.concatenate((np.delete(points,mindist) , [newpt]))
        weights= np.concatenate((np.delete(weights,mindist) , [newwt]))
        generation = np.concatenate((np.delete(generation,mindist),[i]))
        
    return points


def rowify(points0:np.ndarray, horizontal_threshold:float, row_threshold:float ):
    """
    points - input points
    horizontal_thresholds - Minimum horizontal spacing between atoms in the same row
    row_thresholds - Minimum vertical (row) spacing between rows.

    """
    
    assert len(points0.shape)==2,"Data must be 2d"
    assert points0.shape[1]==2,"Data must be 2d"
    
    rows = __row_cluster(points0[:,1],row_threshold,plotit=False)
    
    point_assignments = np.array([np.argmin(abs(rows - xx)) for xx in points0[:,1]])
    
    all_columns = []
    all_atoms = []
    
    for ind in range(len(rows)):
        points_in = np.where(point_assignments==ind)[0]
        
        column = __row_cluster(points0[points_in,0],horizontal_threshold,plotit=False)
        all_columns.append(column)
        
        all_atoms += [(xx,rows[ind]) for xx in column]
    
    all_atoms = np.array(all_atoms)
    
    # Determine point assignments to atoms...
    assignments_F = []
    assignments_R = {ind:[] for ind in range(all_atoms.shape[0])}
    RMS_error = 0
    for ind in range(points0.shape[0]):
        dist = (points0[ind,0] - all_atoms[:,0])**2 + (points0[ind,1] - all_atoms[:,1])**2
        assignments_F.append(np.argmin(dist))
        assignments_R[np.argmin(dist)].append(ind)
        
        RMS_error += np.min(dist)
        
    ERROR_OUT = np.sqrt(RMS_error / points0.shape[0])
    return all_atoms, assignments_F, assignments_R,ERROR_OUT



def logical_to_physical(positions:list[tuple[float,float]], graph:nx.Graph,radius:float = 7.0):
    """
    Map a logical unit disk graph to a rowified and scaled graph

    Parameters
    ----------
    positions : list[tuple[float,float]]
        Positions of each vertex
    graph : nx.Graph
        The unit disk graph represented by the positions.
    radius : float, optional
        The associated blockade radius. The default is 7.0.

    Raises
    ------
    NotImplementedError
        Occurs if there is a many-to-one map of multiple vertices to
         a single atom.

    Returns
    -------
    positions_out : list[list[float,float]]
        Positions of each atom, ordered as a one-to-one map of the original positions.

    """
    # First compute the unit disk radius
    Rudg,rmin,rmax = find_UDG_radius(positions,graph)
    
    positions0 = np.array(positions) * (radius / Rudg)
    
    positions_rowified,assignments_F,assignements_R,_ = rowify(positions0,4.0,4.0)
    
    if len(positions0)!=len(positions_rowified):
        raise NotImplementedError("The rowified map is many-to-one from vertices to atoms!")
    
    # Make sure the rowified positions are ordered in the same
    # way as the original positions.
    positions_out = [positions_rowified[ind].round(1).tolist() for ind in assignments_F]
    
    return positions_out
    
    
    
    
