from . import sequence
from .field import SpatialModulationBuilder
from ..ir.pulse import FieldName

class FieldNameBuilder:

    def __init__(self, sequence) -> None:
        self.sequence = sequence
        self._field_name = None

    @property
    def field_name(self):
        if self._field_name is None:
            raise ValueError('unexpected pipe, expect field name')
        return self._field_name

class RabiBuilder(FieldNameBuilder):

    def __init__(self, sequence) -> None:
        super().__init__(sequence)

    def amplitude(self):
        self._field_name = FieldName.RabiFrequencyAmplitude
        return SpatialModulationBuilder(self)

    def phase(self):
        self._field_name = FieldName.RabiFrequencyPhase
        return SpatialModulationBuilder(self)

class DetuningBuilder(FieldNameBuilder):
    
    def __init__(self, sequence) -> None:
        super().__init__(sequence)
        self._field_name = FieldName.Detuning
