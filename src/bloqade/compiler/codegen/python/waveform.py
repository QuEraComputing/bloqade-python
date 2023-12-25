from decimal import Decimal
from bloqade.ir.visitor import BloqadeIRVisitor
import bloqade.ir.control.waveform as waveform
from bloqade.compiler.analysis.python.waveform import WaveformScanResult
from beartype.typing import Optional
from random import randint


class CodegenPythonWaveform(BloqadeIRVisitor):
    def __init__(
        self,
        scan_result: WaveformScanResult,
        time_str: str = "time",
        indent_level: int = 0,
        jit_compiled: bool = True,
    ):
        self.jit_compiled = jit_compiled
        self.time_str = time_str
        self.bindings = dict(scan_result.bindings)
        self.imports = dict(scan_result.imports)
        self.exprs = []
        self.head_binding = None
        self.indent_level = indent_level
        self.indent_expr = "    " * (self.indent_level + 1)
        self.indent_func = "    " * self.indent_level

    @staticmethod
    def gen_func_binding():
        func_binding = f"__bloqade_waveform_{randint(0, 2**32)}"
        while func_binding in globals():
            func_binding = f"__bloqade_waveform_{randint(0, 2**32)}"

        return func_binding

    def generic_visit(self, node: waveform.Waveform):
        super().generic_visit(node)
        self.head_binding = self.bindings[node]

    def visit_waveform_Constant(self, node: waveform.Constant):
        self.exprs.append(f"{self.indent_expr}{self.bindings[node]} = {node.value()}")

    def visit_waveform_Linear(self, node: waveform.Linear):
        slope = (node.stop - node.start) / node.duration

        self.exprs.append(
            f"{self.indent_expr}{self.bindings[node]} = "
            f"{slope()} * ({self.time_str}) + {node.start()}"
        )

    def visit_waveform_Poly(self, node: waveform.Poly):
        coeff_values = [coeff() for coeff in node.coeffs]
        binding = self.bindings[node]

        terms = [str(coeff_values[0])] + [
            f"{coeff} * ({self.time_str}) ** {p}"
            for p, coeff in enumerate(coeff_values[1:], 1)
        ]
        term_sum = " + ".join(terms)
        self.exprs.append(f"{self.indent_expr}{binding} = {term_sum}")

    def visit_waveform_PythonFn(self, node: waveform.PythonFn):
        from numba import njit

        sorted_parameters = sorted(node.parameters, key=lambda p: p.name)

        args = ", ".join(
            [f"{param.name} = {param.value}" for param in sorted_parameters]
        )
        func_binding = self.gen_func_binding()

        globals()[func_binding] = njit(node.fn) if self.jit_compiled else node.fn

        if args:
            self.exprs.append(
                f"{self.indent_expr}{self.bindings[node]} = "
                f"{func_binding}({self.time_str}, {args})"
            )
        else:
            self.exprs.append(
                f"{self.indent_expr}{self.bindings[node]} = "
                f"{func_binding}({self.time_str})"
            )

    def visit_waveform_Add(self, node: waveform.Add):
        self.visit(node.left)
        self.visit(node.right)

        left_duration = node.left.duration()
        right_duration = node.right.duration()

        if left_duration == right_duration:
            self.exprs.append(
                f"{self.indent_expr}{self.bindings[node]} = "
                f"{self.bindings[node.left]} + {self.bindings[node.right]}"
            )
        elif left_duration > right_duration:
            self.exprs.append(
                f"{self.indent_expr}{self.bindings[node]} = "
                f"{self.bindings[node.left]} + {self.bindings[node.right]} "
                f"if {self.time_str} < {right_duration} else {self.bindings[node.left]}"
            )
        else:
            self.exprs.append(
                f"{self.indent_expr}{self.bindings[node]} = "
                f"{self.bindings[node.left]} + {self.bindings[node.right]} "
                f"if {self.time_str} < {left_duration} else {self.bindings[node.right]}"
            )

    def visit_waveform_Negative(self, node: waveform.Negative):
        self.visit(node.waveform)
        self.exprs.append(
            f"{self.indent_expr}{self.bindings[node]} = -{self.bindings[node.waveform]}"
        )

    def visit_waveform_Scale(self, node: waveform.Scale):
        self.visit(node.waveform)
        self.exprs.append(
            f"{self.indent_expr}{self.bindings[node]} = "
            f"{node.scalar()} * {self.bindings[node.waveform]}"
        )

    def visit_waveform_Slice(self, node: waveform.Slice):
        shift = node.interval.start() if node.interval.start else Decimal("0")

        compiler = CodegenPythonWaveform(
            WaveformScanResult(self.bindings, self.imports),
            time_str=f"{self.time_str} + {shift}",
            indent_level=self.indent_level,
        )

        compiler.visit(node.waveform)

        self.exprs.extend(compiler.exprs)
        self.exprs.append(
            f"{self.indent_expr}{self.bindings[node]} = "
            f"{compiler.bindings[node.waveform]}"
        )

    def visit_waveform_Append(self, node: waveform.Append):
        time_shift = Decimal("0")

        wf = node.waveforms[0]

        compiler = CodegenPythonWaveform(
            WaveformScanResult(self.bindings, self.imports),
            time_str=f"{self.time_str} - {time_shift}",
            indent_level=self.indent_level + 1,
        )

        compiler.visit(wf)
        time_shift += wf.duration()
        self.exprs.append(f"{self.indent_expr}if {self.time_str} < {time_shift}:")
        self.exprs.extend(compiler.exprs)
        self.exprs.append(
            f"{compiler.indent_expr}{self.bindings[node]} = {compiler.head_binding}"
        )

        for wf in node.waveforms[1:]:
            compiler = CodegenPythonWaveform(
                WaveformScanResult(self.bindings, self.imports),
                time_str=f"{self.time_str} - {time_shift}",
                indent_level=self.indent_level + 1,
            )

            compiler.visit(wf)
            time_shift += wf.duration()
            self.exprs.append(
                f"{self.indent_expr}elif {self.time_str} <= {time_shift}:"
            )
            self.exprs.extend(compiler.exprs)
            self.exprs.append(
                f"{compiler.indent_expr}{self.bindings[node]} = {compiler.head_binding}"
            )

        self.exprs.append(f"{self.indent_expr}else:")
        self.exprs.append(f"{compiler.indent_expr}{self.bindings[node]} = 0")

    def emit_func(self, node, func_binding: Optional[str] = None) -> str:
        func_binding = self.gen_func_binding() if func_binding is None else func_binding
        self.visit(node)
        body = "\n".join(self.exprs)

        func = (
            f"def {func_binding}(time):\n"
            f"    if time > {node.duration()}:"
            f"\n        return 0"
            f"\n{body}"
            f"\n    return {self.head_binding}"
        )
        func_code = self.indent_func + func.replace("\n", "\n" + self.indent_func)
        return func_binding, func_code

    def compile(self, node):
        func_binding, func = self.emit_func(node)
        imports = "\n".join(
            [
                f"from {module} import {', '.join(funcs)}"
                for module, funcs in self.imports.items()
            ]
        )

        if self.jit_compiled:
            func = (
                f"{imports}"
                f"\nfrom numba import njit, float64"
                f"\n\n"
                f"@njit(float64(float64))"
                f"\n{func}"
            )
        else:
            func = f"{imports}\n\n{func}"

        exec(func, globals())

        return globals()[func_binding]
