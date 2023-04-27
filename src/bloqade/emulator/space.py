from numpy.typing import NDArray
from typing import List, Tuple
import numpy as np


class Space:    
    pass

class FullSpace(Space):
    n_atom: int   
    
    def get_nz_indices(self, new_configurations):
        return new_configurations

class SubSpace(Space):
    n_atom: int
    configurations: NDArray
    
    def get_nz_indices(self, new_configurations):
        potential_indices = np.searchsorted(new_configurations)
        return potential_indices[potential_indices < self.configurations.size]
        

def get_space(atom_coordinates: List[Tuple[float]], blockade_radius = 0.0, n_level = 2):
    def is_rydberg_state(configurations, index, n_level):
        if n_level == 2:
            return (configurations >> index) & 1 == 1
        else:
            return (configurations // (n_level**index)) % n_level == (n_level - 1)

    n_atom = len(atom_coordinates)
    check_atoms = []
        
    for index_1, position_1 in enumerate(atom_coordinates):
        position_1 = np.asarray(position_1)
        atoms = []
        for index_2, position_2 in enumerate(atom_coordinates[index_1+1:],index_1+1):
            position_2 = np.asarray(position_2)
            if np.linalg.norm(position_1 - position_2) <= blockade_radius:
                atoms.append(index_2)

        check_atoms.append(atoms)
        

    if all(len(sub_list)==0 for sub_list in check_atoms):
        return FullSpace(n_atom, n_level)

    Ns = n_level ** n_atom
    if n_atom > 32:
        raise ValueError("Simulator doesn't support simulations with more than 32 atoms. ")

    configurations = np.arange(Ns,dtype=np.min_scalar_type(Ns-1))

    for index_1,indices in enumerate(check_atoms):
        # get which configurations are in rydberg state for the current index.
        rydberg_configs_1 = is_rydberg_state(configurations, index_1, n_level)
        for index_2 in indices: # loop over neighbors within blockade radius
            # get which configus have the neighbor with a rydberg excitation
            rydberg_configs_2 = is_rydberg_state(configurations, index_2, n_level)
            # get which states do not violate constraint
            mask = np.logical_not(
                np.logical_and(
                        rydberg_configs_1, 
                        rydberg_configs_2
                    )
                )
            # remove states that violate blockade constraint
            configurations = configurations[mask]
            rydberg_configs_1 = rydberg_configs_1[mask]
            
    return SubSpace(n_atom, n_level, configurations)
    
