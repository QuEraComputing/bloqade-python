from bloqade.ir.routine.base import Routine
from bloqade.ir.control.waveform import Waveform, Linear, Constant
from bloqade.builder.typing import ScalarType
from beartype import beartype
from beartype.typing import TYPE_CHECKING, List, Optional, Union, Dict, Any
from decimal import Decimal

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

    capabilities_schema = get_capabilities()

    capabilities = capabilities_schema.capabilities

    # manually convert to units
    return capabilities.scale_units(Decimal("1e6"), Decimal("1e-6"))


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
