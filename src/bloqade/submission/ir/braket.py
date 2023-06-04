import braket.ir.ahs as braket_ir
from braket.task_result import AnalogHamiltonianSimulationTaskResult
from bloqade.submission.ir.task_results import (
    QuEraTaskResults,
    QuEraTaskStatusCode,
    QuEraShotResult,
    QuEraShotStatusCode,
)

from bloqade.submission.ir.task_specification import (
    QuEraTaskSpecification,
    GlobalField,
    LocalField,
)
from typing import Union
from pydantic import BaseModel


class BraketTaskSpecification(BaseModel):
    nshots: int
    program: braket_ir.Program


def to_physical_field(
    quera_field: Union[GlobalField, LocalField]
) -> braket_ir.PhysicalField:
    match quera_field:
        case GlobalField(times=times, values=values):
            time_series = braket_ir.TimeSeries(times=times, values=values)
            return braket_ir.PhysicalField(pattern="uniform", time_series=time_series)

        case LocalField(times=times, values=values, lattice_site_coefficients=pattern):
            time_series = braket_ir.TimeSeries(times=times, values=values)
            return braket_ir.PhysicalField(pattern=pattern, time_series=time_series)

        case _:
            raise TypeError


def extract_braket_program(quera_task_ir: QuEraTaskSpecification):
    setup = braket_ir.Setup(
        ahs_register=braket_ir.AtomArrangement(
            sites=quera_task_ir.lattice.sites,
            filling=quera_task_ir.lattice.filling,
        )
    )

    rabi_amplitude = (
        quera_task_ir.effective_hamiltonian.rydberg.rabi_frequency_amplitude.global_
    )
    rabi_phase = (
        quera_task_ir.effective_hamiltonian.rydberg.rabi_frequency_amplitude.global_
    )
    global_detuning = quera_task_ir.effective_hamiltonian.rydberg.detuning.global_
    local_detuning = quera_task_ir.effective_hamiltonian.rydberg.detuning.local

    if local_detuning:
        shifting_field = [to_physical_field(local_detuning)]
    else:
        shifting_field = []

    driving_field = braket_ir.DrivingField(
        amplitude=to_physical_field(rabi_amplitude),
        phase=to_physical_field(rabi_phase),
        detuning=to_physical_field(global_detuning),
    )

    hamiltonian = braket_ir.Hamiltonian(
        drivingFields=[driving_field], shiftingFields=shifting_field
    )

    return braket_ir.Program(setup=setup, hamiltonian=hamiltonian)


def to_braket_task_ir(quera_task_ir: QuEraTaskSpecification) -> BraketTaskSpecification:
    braket_program_ir = extract_braket_program(quera_task_ir)

    nshots = quera_task_ir.nshots

    return BraketTaskSpecification(nshots=nshots, program=braket_program_ir)


def from_braket_task_results(
    braket_task_results: AnalogHamiltonianSimulationTaskResult,
) -> QuEraTaskResults:
    shot_outputs = []
    for measurement in braket_task_results.measurements:
        shot_outputs.append(
            QuEraShotResult(
                shot_status=QuEraShotStatusCode.Completed,
                pre_sequence=list(measurement.pre_sequence),
                post_sequence=list(measurement.post_sequence),
            )
        )

    return QuEraTaskResults(
        task_status=QuEraTaskStatusCode.Completed, shot_outputs=shot_outputs
    )


def from_braket_status_codes(braket_message: str) -> QuEraTaskStatusCode:
    match braket_message:
        case str("CREATED"):
            return QuEraTaskStatusCode.Created

        case str("RUNNING"):
            return QuEraTaskStatusCode.Running

        case str("COMPLETED"):
            return QuEraTaskStatusCode.Completed

        case str("FAILED"):
            return QuEraTaskStatusCode.Failed

        case str("CANCELLED"):
            return QuEraTaskStatusCode.Cancelled

        case _:
            raise ValueError(f"unexpected argument {braket_message}")
