# -*- coding: utf-8 -*-
"""
Created on Wed Jul 26 13:00:15 2023

@author: jwurtz
"""

import numpy as np

def connected_correlation(bitstrings:list[list[int]]):
    """
    Compute the connected correlation function given bitstrings
    Bitstring is an array of dimension
    [ natoms , nsamples ].
    
    Returns an [natoms , natoms] array which is the connected correlation function
     of the dataset, normalized to be between +/-1.

    """
    
    bitstrings = np.array(bitstrings)
    
    assert bitstrings.min()>=0 and bitstrings.max()<=1," Bitstrings must be bounded between 0 and 1"
    assert bitstrings.dtype==int,"Bitstrings must be integers"
    
    spin = 2*bitstrings - 1
    
    avg = np.average(spin,1)
    cor = np.einsum("ax,bx->ab",spin,spin) / spin.shape[1]
    
    return cor - np.outer(avg,avg)

def density(bitstrings:list[list[int]]):
    """
    Compute the density of Rydberg state of given bitstrings.
    Density 1 means a 100% probability of measuring Rydberg.
    Bitstring is an array of dimension
    [ natoms , nsamples ].
    
    Returns an [natoms , natoms] array which is the connected correlation function
     of the dataset

    """
    
    bitstrings = np.array(bitstrings)
    
    assert bitstrings.min()>=0 and bitstrings.max()<=1," Bitstrings must be bounded between 0 and 1"
    assert bitstrings.dtype==int,"Bitstrings must be integers"
    
    return np.average( 1- bitstrings)