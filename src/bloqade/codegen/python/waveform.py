from decimal import Decimal
from bloqade.ir.visitor.waveform import WaveformVisitor
import bloqade.ir.control.waveform as waveform
from bloqade.analysis.python.waveform import WaveformScanResult


class CodegenPythonWaveform(WaveformVisitor):
    def __init__(
        self,
        scan_result: WaveformScanResult,
        time_str: str = "time",
        indent_level: int = 0,
    ):
        self.time_str = time_str
        self.bindings = scan_result.bindings
        self.imports = scan_result.imports
        self.exprs = []
        self.head_binding = None
        self.indent_level = indent_level
        self.indent_expr = "    " * (self.indent_level + 1)
        self.indent_func = "    " * self.indent_level

    def visit(self, ast: waveform.Waveform):
        super().visit(ast)
        self.head_binding = self.bindings[ast]

    def visit_constant(self, ast: waveform.Constant):
        self.exprs.append(f"{self.indent_expr}{self.bindings[ast]} = {ast.value}")

    def visit_linear(self, ast: waveform.Linear):
        slope = ast.stop - ast.start / ast.duration

        self.exprs.append(
            f"{self.indent_expr}{self.bindings[ast]} = "
            f"{slope()} * ({self.time_str}) + {ast.start()}"
        )

    def visit_poly(self, ast: waveform.Poly):
        coeff_values = [coeff() for coeff in ast.coeffs]
        binding = self.bindings[ast]

        terms = [str(coeff_values[0])] + [
            f"{coeff} * ({self.time_str}) ** {p}"
            for p, coeff in enumerate(coeff_values[1:], 1)
        ]
        term_sum = " + ".join(terms)
        self.exprs.append(f"{self.indent_expr}{binding} = {term_sum}")

    def visit_python_fn(self, ast: waveform.PythonFn):
        args = ", ".join([f"{param.name} = {param.value}" for param in ast.parameters])
        self.exprs.append(
            f"{self.indent_expr}{self.bindings[ast]} = "
            f"{ast.name}({self.time_str}, {args})"
        )

    def visit_add(self, ast: waveform.Add):
        self.visit(ast.left)
        self.visit(ast.right)

        left_duration = ast.left.duration()
        right_duration = ast.right.duration()

        if left_duration == right_duration:
            self.exprs.append(
                f"{self.indent_expr}{self.bindings[ast]} = "
                f"{self.bindings[ast.left]} + {self.bindings[ast.right]}"
            )
        elif left_duration > right_duration:
            self.exprs.append(
                f"{self.indent_expr}{self.bindings[ast]} = "
                f"{self.bindings[ast.left]} + {self.bindings[ast.right]} "
                f"if {self.time_str} < {right_duration} else {self.bindings[ast.left]}"
            )
        else:
            self.exprs.append(
                f"{self.indent_expr}{self.bindings[ast]} = "
                f"{self.bindings[ast.left]} + {self.bindings[ast.right]} "
                f"if {self.time_str} < {left_duration} else {self.bindings[ast.right]}"
            )

    def visit_negative(self, ast: waveform.Negative):
        self.visit(ast.waveform)
        self.exprs.append(
            f"{self.indent_expr}{self.bindings[ast]} = -{self.bindings[ast.waveform]}"
        )

    def visit_scale(self, ast: waveform.Scale):
        self.visit(ast.waveform)
        self.exprs.append(
            f"{self.indent_expr}{self.bindings[ast]} = "
            f"{ast.scalar()} * {self.bindings[ast.waveform]}"
        )

    def visit_slice(self, ast: waveform.Slice):
        shift = ast.interval.start() if ast.interval.start else Decimal("0")

        compiler = CodegenPythonWaveform(
            WaveformScanResult(self.bindings, self.imports),
            time_str=f"{self.time_str} + {shift}",
            indent_level=self.indent_level,
        )

        compiler.visit(ast.waveform)

        self.exprs.extend(compiler.exprs)
        self.exprs.append(
            f"{self.indent_expr}{self.bindings[ast]} = "
            f"{compiler.bindings[ast.waveform]}"
        )

    def visit_append(self, ast: waveform.Append):
        time_shift = Decimal("0")

        wf = ast.waveforms[0]

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
            f"{compiler.indent_expr}{self.bindings[ast]} = {compiler.head_binding}"
        )

        for wf in ast.waveforms[1:]:
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
                f"{compiler.indent_expr}{self.bindings[ast]} = {compiler.head_binding}"
            )

        self.exprs.append(f"{self.indent_expr}else:")
        self.exprs.append(f"{compiler.indent_expr}{self.bindings[ast]} = 0")

    def emit_func(self, ast) -> str:
        self.visit(ast)
        body = "\n".join(self.exprs)

        func = (
            f"def {self.head_binding}(time):\n"
            f"    if time < {ast.duration()}:"
            f"\n        return 0"
            f"\n{body}"
            f"\n    return {self.head_binding}"
        )

        return self.indent_func + func.replace("\n", "\n" + self.indent_func)

    def compile(self, ast, numba_compile: bool = True):
        func = self.emit_func(ast)
        imports = "\n".join(
            [
                f"from {module} import {', '.join(funcs)}"
                for module, funcs in self.imports.items()
            ]
        )

        if numba_compile:
            func = (
                f"{imports}"
                f"\nfrom numba import njit, float64"
                f"\n"
                f"\n"
                f"@njit(float64(float64))"
                f"\n{func}"
            )
        else:
            func = f"{imports}\n\n{func}"

        exec(func, globals())

        return globals()[self.head_binding]
