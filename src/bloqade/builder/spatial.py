from beartype.typing import Optional, TYPE_CHECKING

from beartype import beartype
from beartype.typing import List, Union
from bloqade.builder.typing import ScalarType, LiteralType
from bloqade.builder.waveform import WaveformAttachable
from bloqade.builder.base import Builder


if TYPE_CHECKING:
    from bloqade.ir.control.field import (
        UniformModulation,
        ScaledLocations,
        AssignedRunTimeVector,
        RunTimeVector,
    )


class SpatialModulation(WaveformAttachable):
    pass


class Uniform(SpatialModulation):
    """
    Program node specifying a uniform spacial modulation in the program. Please refer to the
    [`uniform`][bloqade.builder.field.Field.uniform] attribute for more information on
    how to reach this node and steps to further build your program from this node.
    """

    def __bloqade_ir__(self) -> "UniformModulation":
        from bloqade.ir import Uniform

        return Uniform


class Location(SpatialModulation):
    """
    Program node specifying a non-uniform spatial modulation in the program. Please refer to the
    [`location`][bloqade.builder.field.Field.location] method for more information on
    how to reach this node and steps to further build your program from this node.
    """

    @beartype
    def __init__(
        self,
        labels: List[int],
        scales: List[ScalarType],
        parent: Optional[Builder] = None,
    ) -> None:
        from bloqade.ir.scalar import cast
        from bloqade.ir.control.field import Location

        super().__init__(parent)
        self._scaled_locations = {
            Location(label): cast(scale) for label, scale in zip(labels, scales)
        }

    def __bloqade_ir__(self) -> "ScaledLocations":
        from bloqade.ir import ScaledLocations

        return ScaledLocations(self._scaled_locations)


class Scale(SpatialModulation):
    """
    Program node specifying a non-uniform spatial modulation in the program. Please refer to the
    [`scale`][bloqade.builder.field.Field.scale] method for more information on
    how to reach this node and steps to further build your program from this node.
    """

    @beartype
    def __init__(
        self,
        name_or_list: Union[str, List[LiteralType]],
        parent: Optional[Builder] = None,
    ) -> None:
        super().__init__(parent)
        self._name_or_list = name_or_list

    def __bloqade_ir__(self) -> Union["RunTimeVector", "AssignedRunTimeVector"]:
        from bloqade.ir import RunTimeVector, AssignedRunTimeVector

        if isinstance(self._name_or_list, str):
            return RunTimeVector(self._name_or_list)
        else:
            return AssignedRunTimeVector(None, self._name_or_list)
