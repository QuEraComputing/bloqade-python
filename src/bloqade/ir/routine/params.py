from pydantic.dataclasses import dataclass
from typing import Dict, List, Tuple, Union
from decimal import Decimal


ParamType = Union[Decimal, List[Decimal]]


@dataclass(frozen=True)
class Params:
    static_params: Dict[str, ParamType]
    batch_params: List[Dict[str, ParamType]]
    args_list: Tuple[str, ...]

    def parse_args(self, *args) -> Dict[str, Decimal]:
        if len(args) != len(self.args_list):
            raise ValueError(
                f"Expected {len(self.args_list)} arguments, got {len(args)}."
            )

        args = tuple(map(Decimal, map(str, args)))
        return dict(zip(self.args_list, args))

    def batch_assignments(self, *args) -> List[Dict[str, ParamType]]:
        flattened_args = self.parse_args(*args)
        return [{**flattened_args, **batch} for batch in self.batch_params]

    def __str__(self):
        out = ""
        out += "> Static params:\n"
        for var, litrl in self.static_params.items():
            out += f" :: {var} \n      => {litrl}\n"

        out += "\n> Batch params:\n"
        for lid, pair in enumerate(self.batch_params):
            out += f"- batch {lid}:\n"
            for var, litrl in pair.items():
                out += f"   :: {var}\n       => {litrl}\n"

        out += "\n> Arguments:\n"
        out += "  " + repr(self.args_list)

        return out
