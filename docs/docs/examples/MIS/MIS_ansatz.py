from .ansatz import Ansatz
import numpy as np
from bloqade import start
from bloqade.submission.capabilities import get_capabilities
from scipy.interpolate import CubicSpline
import networkx as nx


class MIS_ansatz(Ansatz):

    def __init__(self, problem, q_hardware, num_shots, blockade_radius, unitdisk_radius, num_time_points) -> None:

        self.num_time_points = num_time_points
        self.num_shots = num_shots
        self.graph = problem.graph
        self.positions = problem.positions
        self.blockade_radius = blockade_radius
        self.unitdisk_radius = unitdisk_radius
        self.q_hardware = q_hardware
    
        # Get parameter bounds 
        caps = get_capabilities()

        self.det_max = caps.capabilities.rydberg.global_.detuning_max / 1E6
        self.det_min = caps.capabilities.rydberg.global_.detuning_min / 1E6

        self.amp_min = caps.capabilities.rydberg.global_.rabi_frequency_min / 1E6
        self.amp_max = caps.capabilities.rydberg.global_.rabi_frequency_max / 1E6

        self.total_time = caps.capabilities.rydberg.global_.time_max * 1E6

        self.duration_list = [f"duration_{i+1}" for i in range(self.num_time_points)]
        self.detuning_list = [f"detuning_{i+1}" for i in range(self.num_time_points+1)]

        #self._ansatz = self.ansatz_linear()

    # TODO: Json this and save 

    def submit(self, params):

        if self.q_hardware == True:
            job = self.ansatz_spline(params).braket(self.num_shots)
        elif self.q_hardware == False:
            job = self.ansatz_spline(params).braket_local_simulator(self.num_shots)
        

        return job.submit()

    def ansatz(self):
        return self.ansatz_linear()


    def ansatz_linear(self):
   
        # Initialize MIS program 
        mis_udg_program = (
            start.add_positions(self.positions.astype(float)).scale(self.blockade_radius/self.unitdisk_radius)
            .rydberg.rabi 
            .amplitude.uniform.piecewise_linear(self.duration_list, [0.] + [self.amp_max] * (self.num_time_points-1)  + [0.])
            .detuning.uniform.piecewise_linear(self.duration_list, self.detuning_list)
        )
        return mis_udg_program
    
    # TODO: generalize code to work with params list, regardless of param names
    
    def ansatz_spline(self, params):
       
        x, y = params[:len(params)//2], params[len(params)//2:]

        def piecewise_spline(time, x, y):
            # Cubic Spline interpolation
            cs = CubicSpline(x, y)
            # Construct piecewise function
            piecewise_func = np.piecewise(time, 
                                        [time < x[0], 
                                        (time >= x[0]) & (time <= x[-1]), 
                                        time > x[-1]], 
                                        [y[0], cs, y[-1]])
            return piecewise_func
        
        mis_udg_program = (
        start.add_positions(self.positions.astype(float)).scale(self.blockade_radius/self.unitdisk_radius)
        .rydberg.rabi
        .amplitude.uniform.piecewise_linear([0.5, 3, 0.5], [0., self.amp_max, self.amp_max, 0.])
        .detuning.uniform.fn(fn=lambda time: piecewise_spline(time, x, y), duration=4).sample(0.05)
        )
        return mis_udg_program

    # TODO: make this non-blocking and save stuff into JSON 
    def get_bitstrings(self, x):
    
        var_list = (self.duration_list + self.detuning_list)

        if self.q_hardware == True:
            job = self.ansatz().assign(**dict(zip(var_list, x))).braket(self.num_shots).submit()
        elif self.q_hardware == False:
            job = self.ansatz().assign(**dict(zip(var_list, x))).braket_local_simulator(self.num_shots).submit()

        # Save to JSON in case anything goes wrong
        job.save_json("job.json")

        return np.array(job.submit().report().bitstrings[0])
    

    # TODO: make this non-blocking and save stuff into JSON 

    def get_bitstrings_spline(self, params):
        
        if self.q_hardware == True:
            job = self.ansatz_spline(params).braket(self.num_shots).submit()
        elif self.q_hardware == False:
            job = self.ansatz_spline(params).braket_local_simulator(self.num_shots).submit()

        # Save to JSON in case anything goes wrong
        job.save_json("job.json")

        # TODO: Put code above into a submit function
        # Load the JSON here? 
        
        return np.array(job.report().bitstrings[0])
        
    def get_solutions(self, x):
        bitstrings = self.get_bitstrings(x)
        return self.post_process_MIS(bitstrings)
    
    def parameter_transform(self, duration_values, detuning_values):

        penalty = 0

        if np.any(duration_values < 0):
            duration_values = np.abs(duration_values)
            penalty += np.sum(np.abs(duration_values))

        if np.sum(duration_values) > self.total_time:
            print(f"Time penalty enforced with time {np.sum(duration_values)}!")
            duration_values = ((duration_values / np.sum(duration_values)) * self.total_time) - 1E-5 # To make sure we are within bounds given numerical errors
            penalty += np.abs(np.sum(duration_values) - self.total_time)

        if np.any(detuning_values < self.det_min):
            penalty += np.sum(np.abs(detuning_values[detuning_values < self.det_min] - self.det_min))**2
            detuning_values[detuning_values < self.det_min] = self.det_min

        if np.any(detuning_values > self.det_max):
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