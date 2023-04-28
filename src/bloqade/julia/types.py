from juliacall import Main, TypeValue  # type: ignore
from typing import TypeVar, List, Dict, Any
from dataclasses import dataclass
from .to_julia import ToJulia

PythonCall = Main.seval("PythonCall")


@dataclass(frozen=True)
class JLTypeVar:
    name: str


class JLType:
    """Superclass for all Julia types."""

    def __init__(self, expr, *typeparams) -> None:
        self.expr = expr
        self.obj = getattr(Main, expr)
        params = []
        for param in typeparams:
            if isinstance(param, JLType):
                params.append(param.obj)
            elif isinstance(param, TypeValue):
                params.append(param)
            else:
                raise Exception(f"Unknown type parameter: {param}")
        self.typeparams = params

    def __call__(self, x) -> Any:
        if self.typeparams:
            jl_type = self.obj[*self.typeparams]
        else:
            jl_type = self.obj
        return PythonCall.pyconvert(jl_type, x)

    def __getitem__(self, *typeparams: Any) -> Any:
        return JLType(self.expr, *typeparams)

    def __repr__(self) -> str:
        repr = self.expr
        if self.typeparams:
            repr += "[" + ",".join(map(str, self.typeparams)) + "]"
        return repr


class JLVectorType(JLType):
    def __init__(self, expr, *typeparams) -> None:
        super().__init__(expr, *typeparams)

    def __call__(self, x: List[ToJulia]) -> Any:
        type = self.obj[*self.typeparams]
        ret = type(Main.undef, len(x))
        for i, v in enumerate(x):
            ret[i] = v.julia()
        return ret

    def __getitem__(self, *typeparams: Any) -> Any:
        assert len(typeparams) == 1
        assert self.typeparams == []
        return JLVectorType(*typeparams)


class JLDictType(JLType):
    def __init__(self, expr, *typeparams) -> None:
        super().__init__(expr, *typeparams)

    def __call__(self, x: Dict[ToJulia, ToJulia]) -> Any:
        type = self.obj[*self.typeparams]
        ret = type()
        for k, v in x.items():
            ret[k.julia()] = v.julia()
        return ret

    def __getitem__(self, *typeparams: Any) -> Any:
        assert len(self.typeparams) + len(typeparams) == 2
        return JLDictType(self.expr, *typeparams)


Int32 = JLType("Int32")
Int64 = JLType("Int64")
Float32 = JLType("Float32")
Float64 = JLType("Float64")
Complex = JLType("Complex")
ComplexF32 = JLType("ComplexF32")
ComplexF64 = JLType("ComplexF64")
String = JLType("String")
Bool = JLType("Bool")
Symbol = JLType("Symbol")
Vector = JLVectorType("Vector")
Dict = JLDictType("Dict")
