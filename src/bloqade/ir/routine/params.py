from pydantic.dataclasses import dataclass
from typing import Dict, List, Tuple, Union
from decimal import Decimal


ParamType = Union[Decimal, List[Decimal]]


@dataclass(frozen=True)
class Params:
    static_params: Dict[str, ParamType] = {}
    batch_params: List[Dict[str, ParamType]] = [{}]
    flatten_params: Tuple[str, ...] = ()

    def parse_args(self, *args) -> Dict[str, Decimal]:
        if len(args) != len(self.flatten_params):
            raise ValueError(
                f"Expected {len(self.flatten_params)} arguments, got {len(args)}."
            )

        args = tuple(map(Decimal, map(str, args)))
        return dict(zip(self.flatten_params, args))

    def batch_assignments(self, *args) -> List[Dict[str, ParamType]]:
        return [{**self.parse_args(*args), **batch} for batch in self.batch_params]
