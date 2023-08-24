from .ansatz import Ansatz
import numpy as np
from bloqade import start
from bloqade.submission.capabilities import get_capabilities
from scipy.interpolate import CubicSpline
import networkx as nx
from bloqade.builder.emit import Emit


class MIS_ansatz(Ansatz):

    def __init__(self, problem, backend, num_shots, blockade_radius, unitdisk_radius, ansatz_type, config_path=None,) -> None:
        
        super().__init__(backend_info={"backend": backend, "num_shots": num_shots, "config_path": config_path})

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

        # TODO: pass this in as parameters

        self.t1 = 0.5
        self.t2 = 3
        self.t3 = 0.5

    def ansatz(self, params)->Emit:

        if self.ansatz_type == "linear":
            return self._ansatz_linear(params)
        elif self.ansatz_type == "spline":
            return self._ansatz_spline(params)
        else: 
            NameError("This is not a valid ansatz name!")

    def _ansatz_linear(self, params):

        durations = params[:3]
        detunings = params[3:]
   
        # Initialize MIS program 
        mis_udg_program = (
            start.add_positions(self.positions.astype(float)).scale(self.blockade_radius/self.unitdisk_radius)
            .rydberg.rabi 
            .amplitude.uniform.piecewise_linear(durations, [0., self.amp_max, self.amp_max, 0.])
            .detuning.uniform.piecewise_linear(durations, detunings)
        )
        return mis_udg_program
    
    def _ansatz_spline(self, params):
       
        x, y = params[:len(params)//2], params[len(params)//2:]
    
        mis_udg_program = (
        start.add_positions(self.positions.astype(float)).scale(self.blockade_radius/self.unitdisk_radius)
        .rydberg.rabi
        .amplitude.uniform.piecewise_linear([self.t1, self.t2, self.t3], [0., self.amp_max, self.amp_max, 0.])
        .detuning.uniform.fn(fn=lambda time: self._piecewise_spline(time, [self.t1] + list(x) + [self.t1+self.t2], [-20.] + list(y) + [20.]), duration=self.total_time).sample(0.05)
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

    def parameter_transform(self, parameter_values):

        in_range = True
        penalty = 0

        if self.ansatz_type == "linear":

            duration_values = np.array(parameter_values[:3])
            detuning_values = np.array(parameter_values[3:])

            if np.any(duration_values < 0):
                print("Negative time encountered, pentalty term added!")
                # penalty += np.sum(np.abs(duration_values))
                # duration_values = np.abs(duration_values)

                penalty += 1
                in_range = False

            elif np.sum(duration_values) > self.total_time:
                print(f"Time penalty enforced with time {np.sum(duration_values)}!")
                # penalty += np.abs(np.sum(duration_values) - self.total_time)
                # duration_values = ((duration_values / np.sum(duration_values)) * self.total_time) - 1E-5 # To make sure we are within bounds given numerical errors
                
                penalty += 1
                in_range = False

            elif np.any(detuning_values < self.det_min):
                print("Detuning out of bounds, penalty term added!")
                # penalty += np.sum(np.abs(detuning_values[detuning_values < self.det_min] - self.det_min))**2
                # detuning_values[detuning_values < self.det_min] = self.det_min
                penalty += 1
                in_range = False

            elif np.any(detuning_values > self.det_max):
                print("Detuning out of bounds, penalty term added!")
                # penalty += np.sum(np.abs(detuning_values[detuning_values > self.det_max] - self.det_max))**2
                #detuning_values[detuning_values > self.det_max] = self.det_max
                penalty += 1
                in_range = False
            
            transformed_parameter_values = list(duration_values) + list(detuning_values)
            return in_range, transformed_parameter_values, penalty
    
        elif self.ansatz_type == "spline":

            x = parameter_values[:len(parameter_values)//2]
            y = parameter_values[len(parameter_values)//2:]

            if np.all(np.diff(x) > 0) == False:
                penalty += 1
                in_range = False

            elif x[0] <= self.t1:
                penalty += 1
                in_range = False

            elif x[0] >= self.t1 + self.t2:
                penalty += 1
                in_range = False

            elif x[1] >= self.t1 + self.t2:
                penalty +=1
                in_range = False

            elif self._is_monotonic_increasing(x, y) == False: 
                penalty += 1
                in_range = False

            transformed_parameter_values = list(x) + list(y)

            return in_range, transformed_parameter_values, penalty
        

    def _is_monotonic_increasing(self, x, y):
        t_dense = np.linspace(self.t1, self.t1 + self.t2, 1000)
        spline = CubicSpline([self.t1] + list(x) + [self.t1+self.t2], [-20.] + list(y) + [20.])
        # Evaluate the derivative
        derivative_values = spline(t_dense, 1)  
        # Check if all values are non-negative
        is_monotonic = np.all(derivative_values >= 0)
        return is_monotonic

        
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