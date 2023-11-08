from decimal import Decimal
from bloqade.ir.visitor.waveform import WaveformVisitor
import bloqade.ir.control.waveform as waveform
from bloqade.analysis.python.waveform import WaveformScanResult
from beartype.typing import Optional


class CodegenPythonWaveform(WaveformVisitor):
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
        import random

        func_binding = f"__bloqade_waveform_{random.randint(0, 2**32)}"
        while func_binding in globals():
            func_binding = f"__bloqade_waveform_{random.randint(0, 2**32)}"

        return func_binding

    def visit(self, ast: waveform.Waveform):
        super().visit(ast)
        self.head_binding = self.bindings[ast]

    def visit_constant(self, ast: waveform.Constant):
        self.exprs.append(f"{self.indent_expr}{self.bindings[ast]} = {ast.value()}")

    def visit_linear(self, ast: waveform.Linear):
        slope = (ast.stop - ast.start) / ast.duration

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
        from numba import njit

        args = ", ".join([f"{param.name} = {param.value}" for param in ast.parameters])
        func_binding = self.gen_func_binding()

        globals()[func_binding] = njit(ast.fn) if self.jit_compiled else ast.fn

        if args:
            self.exprs.append(
                f"{self.indent_expr}{self.bindings[ast]} = "
                f"{func_binding}({self.time_str}, {args})"
            )
        else:
            self.exprs.append(
                f"{self.indent_expr}{self.bindings[ast]} = "
                f"{func_binding}({self.time_str})"
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

    def emit_func(self, ast, func_binding: Optional[str] = None) -> str:
        func_binding = self.gen_func_binding() if func_binding is None else func_binding
        self.visit(ast)
        body = "\n".join(self.exprs)

        func = (
            f"def {func_binding}(time):\n"
            f"    if time > {ast.duration()}:"
            f"\n        return 0"
            f"\n{body}"
            f"\n    return {self.head_binding}"
        )
        func_code = self.indent_func + func.replace("\n", "\n" + self.indent_func)
        return func_binding, func_code

    def compile(self, ast):
        func_binding, func = self.emit_func(ast)
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
