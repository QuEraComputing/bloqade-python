from .ansatz import Ansatz
import numpy as np
from bloqade import start
from bloqade.submission.capabilities import get_capabilities
from scipy.interpolate import CubicSpline
import networkx as nx
from bloqade.builder.emit import Emit


class MIS_ansatz(Ansatz):

    def __init__(self, problem, backend, num_shots, blockade_radius, unitdisk_radius, num_time_points, ansatz_type, config_path=None,) -> None:
        
        super().__init__(backend_info={"backend": backend, "num_shots": num_shots, "config_path": config_path})
        self.num_time_points = num_time_points

        self.graph = problem.graph
        self.positions = problem.positions
        self.blockade_radius = blockade_radius
        self.unitdisk_radius = unitdisk_radius
    
        # Get parameter bounds 
        caps = get_capabilities()

        self.det_max = caps.capabilities.rydberg.global_.detuning_max / 1E6
        self.det_min = caps.capabilities.rydberg.global_.detuning_min / 1E6

        self.amp_min = caps.capabilities.rydberg.global_.rabi_frequency_min / 1E6
        self.amp_max = caps.capabilities.rydberg.global_.rabi_frequency_max / 1E6

        self.total_time = caps.capabilities.rydberg.global_.time_max * 1E6

        self.ansatz_type = ansatz_type


    def ansatz(self, params)->Emit:

        if self.ansatz_type == "linear":
            return self._ansatz_linear(params)
        elif self.ansatz_type == "spline":
            return self._ansatz_spline(params)
        else: 
            NameError("This is not a valid ansatz name!")

    def _ansatz_linear(self, params):

        durations = params[:self.num_time_points]
        detunings = params[self.num_time_points:]
   
        # Initialize MIS program 
        mis_udg_program = (
            start.add_positions(self.positions.astype(float)).scale(self.blockade_radius/self.unitdisk_radius)
            .rydberg.rabi 
            .amplitude.uniform.piecewise_linear(durations, [0.] + [self.amp_max] * (self.num_time_points-1)  + [0.])
            .detuning.uniform.piecewise_linear(durations, detunings)
        )
        return mis_udg_program
    
    # TODO: generalize code to work with params list, regardless of param names
    
    def _ansatz_spline(self, params):
       
        x, y = params[:len(params)//2], params[len(params)//2:]
        
        mis_udg_program = (
        start.add_positions(self.positions.astype(float)).scale(self.blockade_radius/self.unitdisk_radius)
        .rydberg.rabi
        .amplitude.uniform.piecewise_linear([0.5, 3, 0.5], [0., self.amp_max, self.amp_max, 0.])
        .detuning.uniform.fn(fn=lambda time: self._piecewise_spline(time, x, y), duration=4).sample(0.05)
        )
        return mis_udg_program
    
    def _piecewise_spline(self, time, x, y):
        # Cubic Spline interpolation
        cs = CubicSpline(x, y)
        # Construct piecewise function
        piecewise_func = np.piecewise(time, 
                                    [time < x[0], 
                                    (time >= x[0]) & (time <= x[-1]), 
                                    time > x[-1]], 
                                    [y[0], cs, y[-1]])
        return piecewise_func
    

    def get_solutions(self, x):
        bitstrings = self.get_bitstrings(x)
        return self.post_process_MIS(bitstrings)
    
    def parameter_transform(self, duration_values, detuning_values):

        penalty = 0

        if np.any(duration_values < 0):
            print("Negative time encountered, pentalty term added!")
            penalty += np.sum(np.abs(duration_values))
            duration_values = np.abs(duration_values)

        if np.sum(duration_values) > self.total_time:
            print(f"Time penalty enforced with time {np.sum(duration_values)}!")
            penalty += np.abs(np.sum(duration_values) - self.total_time)
            duration_values = ((duration_values / np.sum(duration_values)) * self.total_time) - 1E-5 # To make sure we are within bounds given numerical errors

        if np.any(detuning_values < self.det_min):
            print("Detuning out of bounds, penalty term added!")
            penalty += np.sum(np.abs(detuning_values[detuning_values < self.det_min] - self.det_min))**2
            detuning_values[detuning_values < self.det_min] = self.det_min

        if np.any(detuning_values > self.det_max):
            print("Detuning out of bounds, penalty term added!")
            penalty += np.sum(np.abs(detuning_values[detuning_values > self.det_max] - self.det_max))**2
            detuning_values[detuning_values > self.det_max] = self.det_max

        return list(duration_values), list(detuning_values), penalty

        
    def post_process_MIS(self, bitstrings):

        post_processed_bitstrings = []
        for bitstring in bitstrings:
            inds = np.nonzero(bitstring==0)[0]    # Find indices of IS vertices
            subgraph = nx.subgraph(self.graph, inds)  # Generate a subgraph from those vertices.
            if len(subgraph.nodes) == 0:
                post_processed_bitstrings.append(bitstring)
            else: 
                inds2 = nx.maximal_independent_set(subgraph, seed=0)
                payload = np.ones(len(bitstring))     # Forge into the correct data structure (a list of 1s and 0s)
                payload[inds2] = 0
                post_processed_bitstrings.append(payload)
        if len(post_processed_bitstrings) == 0: 
            raise ValueError("no independent sets found! increase number of shots.")

        return np.asarray(post_processed_bitstrings)