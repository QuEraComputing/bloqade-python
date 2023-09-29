from bloqade.builder.args import Args
from bloqade.ir.control.waveform import Waveform, Linear, Constant
from bloqade.builder.typing import ScalarType
from beartype import beartype
from beartype.typing import List, Optional, Union, Dict, Any


@beartype
def linear(duration: ScalarType, start: ScalarType, stop: ScalarType):
    return Linear(start, stop, duration)


@beartype
def constant(duration: ScalarType, value: ScalarType):
    return Constant(value, duration)


@beartype
def piecewise_linear(durations: List[ScalarType], values: List[ScalarType]) -> Waveform:
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
) -> Args:
    from bloqade import start
    from bloqade.atom_arrangement import AtomArrangement

    print(type(atoms_positions))

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

    return prog
