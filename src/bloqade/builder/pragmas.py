from beartype.typing import List, Dict, Union, TYPE_CHECKING
from bloqade.builder.typing import LiteralType, ParamType
from bloqade.ir.scalar import Variable

if TYPE_CHECKING:
    from bloqade.builder.assign import Assign, BatchAssign, ListAssign
    from bloqade.builder.parallelize import Parallelize
    from bloqade.builder.args import Args


class AddArgs:
    def args(self, args_list: List[Union[str, Variable]]) -> "Args":
        from bloqade.builder.args import Args

        return Args(args_list, self)


class Assignable:
    def assign(self, **assignments) -> "Assign":
        """
        Assign values to variables declared previously in the program.

        This is reserved for variables that should only take single values OR
        for spatial modulations that were created with `.var` in which case you can
        pass in a list. This is the ONLY circumstance in which multiple
        values are allowed.

        Usage Examples:
        ```
        # define geometry
        >>> reg = bloqade.start
        ...       .add_position([(0,0),(1,1),(2,2),(3,3)])
        # define variables in program
        >>> seq = reg.rydberg.detuning.uniform
        ...       .linear(start="ival",stop=1,duration="span_time")
        # assign values to variables
        >>> seq = seq.assign(span_time = 0.5, ival = 0.0)
        ```

        - You can now:
            - |_ ...assign(assignments).bloqade: select the bloqade local
                emulator backend
            - |_ ...assign(assignments).braket: select braket local emulator or
                QuEra hardware
            - |_ ...assign(assignments).device(specifier_string): select backend
                by specifying a string
        - Assign multiple values to a single variable for a parameter sweep:
            - |_ ...assign(assignments).batch_assign(assignments):
        - Parallelize the program register, duplicating the geometry and waveform
            sequence to take advantage of all available
          space/qubits on the QPU:
            - |_ ...assign(assignments).parallelize(cluster_spacing)
        - Defer value assignment of certain variables to runtime:
            - |_ ...assign(assignments).args([previously_defined_vars])

        """
        from bloqade.builder.assign import Assign

        return Assign(assignments, parent=self)


class BatchAssignable:
    def batch_assign(
        self,
        __batch_params: List[Dict[str, ParamType]] = [],
        **assignments: List[ParamType],
    ) -> Union["BatchAssign", "ListAssign"]:
        """

        Assign multiple values to a single variable to create a parameter sweep.

        Bloqade automatically handles the multiple programs this would generate
        and treats it as object with unified results for easy post-processing.

        NOTE: if you assign multiple values to multiple variables in your program,
        the values must be of the same length. Bloqade will NOT do a Cartesian product
        (e.g. if "var1" is assigned [1,2,3] and "var2" is assigned [4,5,6] then the
        resulting programs will have assignments [1,4], [2,5], [3,6]).

        Usage Example:
        ```
        >>> reg = start.add_position([(0,0), (0, "atom_distance")])
        >>> prog = reg.rydberg.rabi.amplitude.uniform.constant("value", 5.0)
        >>> var_assigned_prog = prog.batch_assign(value = [1.0, 2.0, 3.0],
        atom_distance = [1.0, 2.0, 3.0])
        ```

        - Next steps are:
            - |_ ...batch_assign(assignments).bloqade: select the bloqade
                local emulator backend
            - |_ ...batch_assign(assignments).braket: select braket local
            emulator or QuEra hardware
            - |_ ...batch_assign(assignments).device(specifier_string): select
            backend by specifying a string
        - Parallelize the program register, duplicating the geometry and waveform
          sequence to take advantage of all available
          space/qubits on the QPU:
            - |_ ...batch_assign(assignments).parallelize(cluster_spacing)
        - Defer value assignment of certain variables to runtime:
            - |_ ...batch_assign(assignments).args([previously_defined_vars])

        """
        from bloqade.builder.assign import BatchAssign, ListAssign

        if len(__batch_params) > 0 and assignments:
            raise ValueError("batch_params and assignments cannot be used together.")

        if len(__batch_params) > 0:
            return ListAssign(__batch_params, parent=self)
        else:
            return BatchAssign(assignments, parent=self)


class Parallelizable:
    def parallelize(self, cluster_spacing: LiteralType) -> "Parallelize":
        """

        Parallelize the current problem (register and sequence) by duplicating
        the geometry to take advantage of all available space/qubits on hardware.

        The singular argument lets you specify how far apart the clusters
        should be in micrometers.

        Usage Example:
        ```
        >>> reg = start.add_position((0,0)).rydberg.rabi.uniform.amplitude
        .constant(1.0, 1.0)
        # copy-paste the geometry and waveforms
        >>> parallelized_prog = reg.parallelize(24)
        ```

        - Your next steps are:
            |_ `...parallelize(cluster_spacing).bloqade`: select the bloqade
                local emulator backend
            |_ `...parallelize(cluster_spacing).braket`: select braket
                local emulator or QuEra hardware on the cloud
            |_ `...parallelize(cluster_spacing).device(specifier_string)`: select
                backend by specifying a string

        """
        from bloqade.builder.parallelize import Parallelize

        return Parallelize(cluster_spacing, self)
