import numpy as np
import plum
from bloqade.ir.location import ListOfLocations
from bloqade.ir.routine.base import Routine
from bloqade.ir.control.waveform import Waveform, Linear, Constant
from bloqade.builder.typing import ScalarType, LiteralType
from beartype import beartype
from beartype.typing import TYPE_CHECKING, List, Optional, Union, Dict, Any, Tuple
from decimal import Decimal
from networkx import Graph

if TYPE_CHECKING:
    from bloqade.submission.ir.capabilities import QuEraCapabilities


def get_capabilities() -> "QuEraCapabilities":
    """Get the device capabilities for Aquila

    Returns:
        QuEraCapabilities: capabilities object for Aquila device.


    Note:
        Units of time, distance, and energy are microseconds (us),
        micrometers (um), and rad / us, respectively.

        For a comprehensive list of capabilities,
        see the [Hardware Reference](../../reference/hardware-capabilities.md)
        page
    """

    from bloqade.submission.capabilities import get_capabilities
    import bloqade.submission.ir.capabilities as cp

    capabilities_schema = get_capabilities()

    capabilities = capabilities_schema.capabilities

    # manually convert to units
    return cp.QuEraCapabilities(
        version=capabilities_schema.version,
        capabilities=cp.DeviceCapabilities(
            task=cp.TaskCapabilities(
                number_shots_max=capabilities.task.number_shots_max,
                number_shots_min=capabilities.task.number_shots_min,
            ),
            lattice=cp.LatticeCapabilities(
                number_qubits_max=capabilities.lattice.number_qubits_max,
                area=cp.LatticeAreaCapabilities(
                    width=(capabilities.lattice.area.width * Decimal("1e6")),  # m
                    height=(capabilities.lattice.area.height * Decimal("1e6")),  # m
                ),
                geometry=cp.LatticeGeometryCapabilities(
                    number_sites_max=capabilities.lattice.geometry.number_sites_max,
                    spacing_radial_min=(
                        capabilities.lattice.geometry.spacing_radial_min
                        * Decimal("1e6")
                    ),  # m
                    spacing_vertical_min=(
                        capabilities.lattice.geometry.spacing_vertical_min
                        * Decimal("1e6")
                    ),  # m
                    position_resolution=(
                        capabilities.lattice.geometry.position_resolution
                        * Decimal("1e6")
                    ),  # m
                ),
            ),
            rydberg=cp.RydbergCapabilities(
                c6_coefficient=capabilities.rydberg.c6_coefficient
                * Decimal("1e30"),  # rad * m^6 / s
                global_=cp.RydbergGlobalCapabilities(
                    phase_max=(capabilities.rydberg.global_.phase_max),  # rad
                    phase_min=(capabilities.rydberg.global_.phase_min),  # rad
                    phase_resolution=(
                        capabilities.rydberg.global_.phase_resolution
                    ),  # rad
                    rabi_frequency_max=(
                        capabilities.rydberg.global_.rabi_frequency_max / Decimal("1e6")
                    ),  # rad / s
                    rabi_frequency_min=(
                        capabilities.rydberg.global_.rabi_frequency_min / Decimal("1e6")
                    ),  # rad / s
                    rabi_frequency_resolution=(
                        capabilities.rydberg.global_.rabi_frequency_resolution
                        / Decimal("1e6")
                    ),  # rad / s
                    rabi_frequency_slew_rate_max=(
                        capabilities.rydberg.global_.rabi_frequency_slew_rate_max
                        / Decimal("1e6") ** 2
                    ),  # rad / s^2
                    detuning_max=(
                        capabilities.rydberg.global_.detuning_max / Decimal("1e6")
                    ),  # rad / s
                    detuning_min=(
                        capabilities.rydberg.global_.detuning_min / Decimal("1e6")
                    ),  # rad / s
                    detuning_resolution=(
                        capabilities.rydberg.global_.detuning_resolution
                        / Decimal("1e6")
                    ),  # rad / s
                    detuning_slew_rate_max=(
                        capabilities.rydberg.global_.detuning_slew_rate_max
                        / Decimal("1e6") ** 2
                    ),  # rad / s^2
                    time_min=(
                        capabilities.rydberg.global_.time_min * Decimal("1e6")
                    ),  # s
                    time_max=(
                        capabilities.rydberg.global_.time_max * Decimal("1e6")
                    ),  # s
                    time_resolution=(
                        capabilities.rydberg.global_.time_resolution * Decimal("1e6")
                    ),  # s
                    time_delta_min=(
                        capabilities.rydberg.global_.time_delta_min * Decimal("1e6")
                    ),  # s
                ),
                local=cp.RydbergLocalCapabilities(
                    number_local_detuning_sites=(
                        capabilities.rydberg.local.number_local_detuning_sites
                    ),
                    site_coefficient_max=(
                        capabilities.rydberg.local.site_coefficient_max
                    ),
                    site_coefficient_min=(
                        capabilities.rydberg.local.site_coefficient_min
                    ),
                    spacing_radial_min=(
                        capabilities.rydberg.local.spacing_radial_min * Decimal("1e6")
                    ),  # rad / s
                    detuning_min=(
                        capabilities.rydberg.local.detuning_min / Decimal("1e6")
                    ),  # rad / s
                    detuning_max=(
                        capabilities.rydberg.local.detuning_max / Decimal("1e6")
                    ),  # rad / s
                    detuning_slew_rate_max=(
                        capabilities.rydberg.local.detuning_slew_rate_max
                        / Decimal("1e6") ** 2
                    ),  # rad / s^2
                    time_delta_min=(
                        capabilities.rydberg.local.time_delta_min * Decimal("1e6")
                    ),  # s
                    time_resolution=(
                        capabilities.rydberg.local.time_resolution * Decimal("1e6")
                    ),  # s
                ),
            ),
        ),
    )


@beartype
def linear(duration: ScalarType, start: ScalarType, stop: ScalarType) -> Linear:
    """Create a Linear waveform.

    Args:
        duration (ScalarType): Duration of linear waveform
        start (ScalarType): Starting value of linear waveform
        stop (ScalarType): Ending value of linear waveform

    Returns:
        Linear: Linear waveform
    """
    return Linear(start, stop, duration)


@beartype
def constant(duration: ScalarType, value: ScalarType) -> Constant:
    """Create a Constant waveform.

    Args:
        duration (ScalarType): Duration of the Constant waveform.
        value (ScalarType): Value of the Constant waveform.s

    Returns:
        Constant: A Constant waveform.
    """
    return Constant(value, duration)


@beartype
def piecewise_linear(durations: List[ScalarType], values: List[ScalarType]) -> Waveform:
    """Create a piecewise linear waveform.

    Create a piecewise linear waveform from a list of durations and values. The
    value `duration[i]` is of the linear segment between `values[i]` and `values[i+1]`.

    Args:
        durations (List[ScalarType]): The duration of each segment
        values (List[ScalarType]): The values for each segment

    Raises:
        ValueError: If the length of `values` is not one greater than the length of
        `durations`.

    Returns:
        Waveform: The piecewise linear waveform.
    """

    if len(durations) + 1 != len(values):
        raise ValueError(
            "The length of values must be one greater than the length of durations"
        )

    pwl_wf = None
    for duration, start, stop in zip(durations, values[:-1], values[1:]):
        if pwl_wf is None:
            pwl_wf = Linear(start, stop, duration)
        else:
            pwl_wf = pwl_wf.append(Linear(start, stop, duration))

    return pwl_wf


@beartype
def piecewise_constant(
    durations: List[ScalarType], values: List[ScalarType]
) -> Waveform:
    """Create a piecewise linear waveform.

    Create a piecewise constant waveform from a list of durations and values. The
    value `duration[i]` corresponds to the length of time for the i'th segment
    with a value of `values[i]`.

    Args:
        durations (List[ScalarType]): The duration of each segment
        values (List[ScalarType]): The values for each segment

    Raises:
        ValueError: If the length of `values` is not the same as the length of
        `durations`.

    Returns:
        Waveform: The piecewise linear waveform.
    """
    if len(durations) != len(values):
        raise ValueError(
            "The length of values must be the same as the length of durations"
        )

    pwc_wf = None
    for duration, value in zip(durations, values):
        if pwc_wf is None:
            pwc_wf = Constant(value, duration)
        else:
            pwc_wf = pwc_wf.append(Constant(value, duration))

    return pwc_wf


@beartype
def rydberg_h(
    atoms_positions: Any,
    detuning: Optional[Waveform] = None,
    amplitude: Optional[Waveform] = None,
    phase: Optional[Waveform] = None,
    static_params: Dict[str, Any] = {},
    batch_params: Union[List[Dict[str, Any]], Dict[str, Any]] = [],
    args: List[str] = [],
) -> Routine:
    """Create a rydberg program with uniform detuning, amplitude, and phase.

    Args:
        atoms_positions (Any): Description of geometry of atoms in system.
        detuning (Optional[Waveform], optional): Waveform for detuning.
            Defaults to None.
        amplitude (Optional[Waveform], optional): Waveform describing the amplitude of
            the rabi term. Defaults to None.
        phase (Optional[Waveform], optional): Waveform describing the phase of rabi
            term. Defaults to None.
        static_params (Dict[str, Any], optional): Define static parameters of your
            program. Defaults to {}.
        batch_params (Union[List[Dict[str, Any]], Dict[str, Any]], optional):
            Parmaters for a batch of tasks. Defaults to [].
        args (List[str], optional): List of arguments to leave till runtime.
            Defaults to [].

    Returns:
        Routine: An object that can be used to dispatch a rydberg program to
            multiple backends.
    """
    from bloqade import start
    from bloqade.atom_arrangement import AtomArrangement

    if isinstance(atoms_positions, AtomArrangement):
        prog = atoms_positions
    else:
        prog = start.add_position(atoms_positions)

    if detuning is not None:
        prog = prog.rydberg.detuning.uniform.apply(detuning)

    if amplitude is not None:
        prog = prog.amplitude.uniform.apply(amplitude)

    if phase is not None:
        prog = prog.phase.uniform.apply(phase)

    prog = prog.assign(**static_params)

    if isinstance(batch_params, dict):
        prog = prog.batch_assign(**batch_params)
    else:
        prog = prog.batch_assign(batch_params)

    prog = prog.args(args)

    return prog.parse()


@plum.dispatch
def from_unit_disk_graph(
    positions: List[Tuple[LiteralType, LiteralType]],
    graph: Graph,
    radius_physical: LiteralType = 7.0,
) -> ListOfLocations:
    """Generates a Physical Geometry given a unit disk graph.

    Args:
        positions (List[Tuple[LiteralType, LiteralType]]): The list of
            positions for the nodes
        graph (Graph): A graph describing the connectivity of the nodes
        radius_physical (LiteralType): The target physical radius
            (in micrometers) of the physical geometry

    Raises:
        ValueError: The provided positions comply with the graph provided

    Returns:
        ListOfLocations: The equivilant physical geometry
    """

    from bloqade import start

    positions = np.asarray(positions)

    rmin = 0
    rmax = np.inf

    dists = {}

    for i, pos_i in enumerate(positions[:]):
        for j, pos_j in enumerate(positions[i + 1 :], i + 1):
            d = dists.get((i, j), np.linalg.norm(pos_i - pos_j))

            if (i, j) in graph.edges:
                rmin = max(rmin, d)
            else:
                rmax = min(rmax, d)

    if rmin > rmax:
        raise ValueError("Positions do not form the unit disk graph specified by graph")

    r_udg = np.sqrt(rmin * rmax)

    return start.add_position(positions).scale(radius_physical / r_udg)
