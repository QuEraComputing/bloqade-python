from decimal import Decimal
from beartype.typing import Tuple


def convert_time_units(time: Decimal) -> Decimal:
    return time * Decimal("1e-6")


def convert_energy_units(energy: Decimal) -> Decimal:
    return energy * Decimal("1e6")


def convert_coordinate_units(
    length: Tuple[Decimal, Decimal]
) -> Tuple[Decimal, Decimal]:
    return (length[0] * Decimal("1e-6"), length[1] * Decimal("1e-6"))
