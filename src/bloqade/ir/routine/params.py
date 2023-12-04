from functools import cached_property
from pydantic.dataclasses import dataclass
from typing import Dict, List, Tuple, Union
from decimal import Decimal


ParamType = Union[Decimal, List[Decimal]]


@dataclass(frozen=True)
class ScalarArg:
    name: str


@dataclass(frozen=True)
class VectorArg:
    name: str


@dataclass(frozen=True)
class Params:
    n_sites: int
    static_params: Dict[str, ParamType]
    batch_params: List[Dict[str, ParamType]]
    args_list: Tuple[Union[ScalarArg, VectorArg], ...]

    @cached_property
    def num_args(self) -> int:
        num_args = 0
        for arg in self.args_list:
            if isinstance(arg, VectorArg):
                # expect n_sites args for vector arguments
                num_args += self.n_sites
            else:
                num_args += 1

        return num_args

    @cached_property
    def arg_names(self) -> Tuple[str]:
        return tuple([arg.name for arg in self.args_list])

    def parse_args(self, *flattened_args) -> Dict[str, Decimal]:
        if len(flattened_args) != self.num_args:
            raise ValueError(
                f"Expected {self.num_args} arguments, got {len(flattened_args)}."
            )

        args = []
        i = 0
        for arg in self.args_list:
            # if arg is a vector, then we need to unpack the next n_sites args
            if isinstance(arg, VectorArg):
                vec = list(map(Decimal, map(str, flattened_args[i : i + self.n_sites])))
                args.append(vec)
                i += self.n_sites
            else:
                args.append(Decimal(str(flattened_args[i])))
                i += 1

        return dict(zip(self.arg_names, args))

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
