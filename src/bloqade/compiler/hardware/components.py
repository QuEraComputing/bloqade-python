from bloqade.codegen.hardware_v2.lattice import AHSLatticeData
from bloqade.codegen.hardware_v2.piecewise_linear import PiecewiseLinear
from bloqade.codegen.hardware_v2.piecewise_constant import PiecewiseConstant
from bloqade.submission.ir.braket import BraketTaskSpecification
from bloqade.submission.ir.parallel import ParallelDecoder
from bloqade.submission.ir.task_specification import QuEraTaskSpecification
from beartype.typing import Optional, List, Tuple
from pydantic.dataclasses import dataclass
from decimal import Decimal


@dataclass
class AHSComponents:
    lattice_data: AHSLatticeData
    global_detuning: PiecewiseLinear
    global_amplitude: PiecewiseLinear
    global_phase: PiecewiseConstant
    local_detuning: Optional[PiecewiseLinear]
    lattice_site_coefficients: Optional[List[Decimal]]

    @staticmethod
    def convert_time_units(time: Decimal) -> Decimal:
        return time * Decimal("1e-6")

    @staticmethod
    def convert_energy_units(energy: Decimal) -> Decimal:
        return energy * Decimal("1e6")

    @staticmethod
    def convert_coordinate_units(
        length: Tuple[Decimal, Decimal]
    ) -> Tuple[Decimal, Decimal]:
        return (length[0] * Decimal("1e-6"), length[1] * Decimal("1e-6"))

    def generate_quera_ir(
        self, shots: int
    ) -> Tuple[QuEraTaskSpecification, Optional[ParallelDecoder]]:
        import bloqade.submission.ir.task_specification as task_spec

        lattice = task_spec.Lattice(
            sites=list(map(self.convert_coordinate_units, self.lattice_data.sites)),
            filling=self.lattice_data.filling,
        )

        global_detuning = task_spec.GlobalField(
            times=list(map(self.convert_time_units, self.global_detuning.times)),
            values=list(map(self.convert_energy_units, self.global_detuning.values)),
        )

        local_detuning = None

        if self.lattice_site_coefficients is not None:
            local_detuning = task_spec.LocalField(
                times=list(map(self.convert_time_units, self.local_detuning.times)),
                values=list(map(self.convert_energy_units, self.local_detuning.values)),
                lattice_site_coefficients=self.lattice_site_coefficients,
            )

        rabi_frequency_amplitude_field = task_spec.GlobalField(
            times=list(map(self.convert_time_units, self.global_amplitude.times)),
            values=list(map(self.convert_energy_units, self.global_amplitude.values)),
        )

        rabi_frequency_phase_field = task_spec.GlobalField(
            times=list(map(self.convert_time_units, self.global_phase.times)),
            values=self.global_phase.values,
        )

        detuning = task_spec.Detuning(
            global_=global_detuning,
            local=local_detuning,
        )

        rabi_frequency_amplitude = task_spec.RabiFrequencyAmplitude(
            global_=rabi_frequency_amplitude_field,
        )

        rabi_frequency_phase = task_spec.RabiFrequencyPhase(
            global_=rabi_frequency_phase_field,
        )

        rydberg = task_spec.RydbergHamiltonian(
            rabi_frequency_amplitude=rabi_frequency_amplitude,
            rabi_frequency_phase=rabi_frequency_phase,
            detuning=detuning,
        )

        effective_hamiltonian = task_spec.EffectiveHamiltonian(
            rydberg=rydberg,
        )

        return (
            task_spec.QuEraTaskSpecification(
                nshots=shots,
                lattice=lattice,
                effective_hamiltonian=effective_hamiltonian,
            ),
            self.lattice_data.parallel_decoder,
        )

    def generate_braket_ir(
        self, shots: int
    ) -> Tuple[BraketTaskSpecification, Optional[ParallelDecoder]]:
        import braket.ir.ahs as ahs
        from bloqade.submission.ir.braket import BraketTaskSpecification

        ahs_register = ahs.AtomArrangement(
            sites=list(map(self.convert_coordinate_units, self.lattice_data.sites)),
            filling=self.lattice_data.filling,
        )

        global_detuning_time_series = ahs.TimeSeries(
            times=list(map(self.convert_time_units, self.global_detuning.times)),
            values=list(map(self.convert_energy_units, self.global_detuning.values)),
        )

        local_detuning_time_series = None
        if self.lattice_site_coefficients is not None:
            local_detuning_time_series = ahs.TimeSeries(
                times=list(map(self.convert_time_units, self.local_detuning.times)),
                values=list(map(self.convert_energy_units, self.local_detuning.values)),
            )

        amplitude_time_series = ahs.TimeSeries(
            times=list(map(self.convert_time_units, self.global_amplitude.times)),
            values=list(map(self.convert_energy_units, self.global_amplitude.values)),
        )

        phase_time_series = ahs.TimeSeries(
            times=list(map(self.convert_time_units, self.global_phase.times)),
            values=self.global_phase.values,
        )

        detuning = ahs.PhysicalField(
            time_series=global_detuning_time_series,
            pattern="uniform",
        )

        amplitude = ahs.PhysicalField(
            time_series=amplitude_time_series,
            pattern="uniform",
        )

        phase = ahs.PhysicalField(
            time_series=phase_time_series,
            pattern="uniform",
        )

        local_detuning = None
        if self.lattice_site_coefficients is not None:
            local_detuning = ahs.PhysicalField(
                time_series=local_detuning_time_series,
                pattern=self.lattice_site_coefficients,
            )

        driving_field = ahs.DrivingField(
            detuning=detuning,
            amplitude=amplitude,
            phase=phase,
        )

        shiftingFields = []
        if self.lattice_site_coefficients is not None:
            shiftingFields = [ahs.ShiftingField(magnitude=local_detuning)]

        program = ahs.Program(
            setup=ahs.Setup(ahs_register=ahs_register),
            hamiltonian=ahs.Hamiltonian(
                drivingFields=[driving_field],
                shiftingFields=shiftingFields,
            ),
        )

        return (
            BraketTaskSpecification(nshots=shots, program=program),
            self.lattice_data.parallel_decoder,
        )
