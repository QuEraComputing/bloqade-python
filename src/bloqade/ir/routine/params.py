from pydantic.dataclasses import dataclass
from typing import Dict, List, Tuple, Union
from decimal import Decimal


ParamType = Union[Decimal, List[Decimal]]


@dataclass(frozen=True)
class Params:
    static_params: Dict[str, ParamType]
    batch_params: List[Dict[str, ParamType]]
    flatten_params: Tuple[str, ...]

    def parse_args(self, *args) -> Dict[str, Decimal]:
        if len(args) != len(self.flatten_params):
            raise ValueError(
                f"Expected {len(self.flatten_params)} arguments, got {len(args)}."
            )

        args = tuple(map(Decimal, map(str, args)))
        return dict(zip(self.flatten_params, args))

    def batch_assignments(self, *args) -> List[Dict[str, ParamType]]:
        flattened_args = self.parse_args(*args)
        return [{**flattened_args, **batch} for batch in self.batch_params]

    def __repr__(self):
        out = "Static assign:\n"
        for var, litrl in self.static_params.items():
            out += f" :: {var} \t= {litrl}\n"

        out += "\nBatch params/assign:\n"
        for lid, pair in enumerate(self.batch_params):
            out += f"- batch {lid}:\n"
            for var, litrl in pair.items():
                out += f"   :: {var} = {litrl}\n"

        out += "\nFlatten params:\n"
        out += "  " + repr(self.flatten_params)

        return out
