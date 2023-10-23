from bloqade.ir.visitor.waveform import WaveformVisitor
import bloqade.ir.control.waveform as waveform
from beartype.typing import Any, Dict, FrozenSet, Set
from pydantic.dataclasses import dataclass


@dataclass(frozen=True)
class WaveformScanResult:
    bindings: Dict[waveform.Waveform, str]
    imports: Dict[str, FrozenSet[str]]


class WaveformScan(WaveformVisitor):
    def __init__(
        self,
        bindings: Dict[waveform.Waveform, str] = {},
        imports: Dict[str, Set[str]] = {},
    ):
        self.bindings = bindings
        self.imports = imports
        self.i = 0

    def add_binding(self, expr: waveform.Waveform):
        if expr in self.bindings:
            pass

        symbol = f"__bloqade_var{self.i}"

        while symbol in self.imports.values() in globals():
            self.i += 1
            symbol = f"__bloqade_var{self.i}"

        self.i += 1

        self.bindings[expr] = symbol

    def visit_constant(self, ast: waveform.Constant):
        pass

    def visit_linear(self, ast: waveform.Linear):
        pass

    def visit_python_fn(self, ast: waveform.PythonFn):
        pass

    def visit_poly(self, ast: waveform.Poly):
        pass

    def visit_add(self, ast: waveform.Add):
        self.visit(ast.left)
        self.visit(ast.right)

    def visit_negative(self, ast: waveform.Negative):
        self.visit(ast.waveform)

    def visit_scale(self, ast: waveform.Scale):
        self.visit(ast.waveform)

    def visit_slice(self, ast: waveform.Slice):
        self.visit(ast.waveform)

    def visit_smooth(self, ast: waveform.Smooth):
        raise NotImplementedError(
            "Smooth is not yet implemented in the waveform compiler"
        )

    def visit_alligned(self, ast: waveform.AlignedWaveform) -> Any:
        raise NotImplementedError(
            "AlignedWaveform is not yet implemented in the waveform compiler"
        )

    def visit_append(self, ast: waveform.Append) -> Any:
        list(map(self.visit, ast.waveforms))

    def visit_record(self, ast: waveform.Record) -> Any:
        raise ValueError("Expecting fully expanded waveform, found Record Node")

    def visit_sample(self, ast: waveform.Sample):
        raise ValueError("Expecting fully expanded waveform, found Sample Node")

    def visit(self, ast: waveform.Waveform):
        self.add_binding(ast)
        super().visit(ast)

    def scan(self, ast: waveform.Waveform) -> WaveformScanResult:
        self.visit(ast)
        imports = {
            module: frozenset(imports) for module, imports in self.imports.items()
        }
        return WaveformScanResult(self.bindings, imports)
