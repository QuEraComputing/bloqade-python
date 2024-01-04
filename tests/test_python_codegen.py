import inspect
from bloqade.compiler.analysis.python.waveform import WaveformScan
from bloqade.compiler.rewrite.python.waveform import NormalizeWaveformPython
from bloqade.compiler.codegen.python.waveform import CodegenPythonWaveform
from bloqade.compiler.rewrite.common.assign_variables import AssignBloqadeIR
from bloqade.factory import piecewise_linear, piecewise_constant
import bloqade.ir.control.waveform as wf
from unittest.mock import patch
import numpy as np
import numba
from bloqade import start


def f(t):
    return np.sin(2 * np.pi * t)


def test_waveform_scan():
    wf1 = wf.Poly([1, 2, 3], 4.0)
    wf2 = wf.Linear(0, 1, 4.0)
    wf3 = wf.Constant(1.0, 4.0)
    wf4 = wf.PythonFn.create(f, 4.0)

    for a_wf in [wf1, wf2, wf3, wf4]:
        scan = WaveformScan().scan(a_wf)

        assert scan.bindings == {a_wf: "__bloqade_var0"}
        assert scan.imports == {}

    wf5 = wf1 + wf2

    scan = WaveformScan().scan(wf5)
    assert scan.bindings == {
        wf5: "__bloqade_var0",
        wf1: "__bloqade_var1",
        wf2: "__bloqade_var2",
    }

    wf6 = 3.0 * wf1

    scan = WaveformScan().scan(wf6)
    assert scan.bindings == {
        wf6: "__bloqade_var0",
        wf1: "__bloqade_var1",
    }

    wf7 = -wf1

    scan = WaveformScan().scan(wf7)
    assert scan.bindings == {
        wf7: "__bloqade_var0",
        wf1: "__bloqade_var1",
    }

    wf8 = wf1[0:1]
    scan = WaveformScan().scan(wf8)
    assert scan.bindings == {
        wf8: "__bloqade_var0",
        wf1: "__bloqade_var1",
    }

    wf9 = wf1.append(wf2)
    scan = WaveformScan().scan(wf9)
    assert scan.bindings == {
        wf9: "__bloqade_var0",
        wf1: "__bloqade_var1",
        wf2: "__bloqade_var2",
    }

    wf10 = wf1 + wf2
    wf11 = wf10 + wf3
    scan = WaveformScan().scan(wf11)
    assert scan.bindings == {
        wf11: "__bloqade_var0",
        wf10: "__bloqade_var1",
        wf1: "__bloqade_var2",
        wf2: "__bloqade_var3",
        wf3: "__bloqade_var4",
    }


def test_waveform_normalize():
    wf1 = wf.Poly([1, 2, 3], 4.0)
    wf2 = wf.Linear(0, 1, 4.0)
    wf3 = wf.Constant(1.0, 4.0)
    wf4 = wf.PythonFn.create(f, 4.0)

    for a_wf in [
        wf1,
        wf2,
        wf3,
        wf4,
        wf1 + wf2,
        2.0 * wf1,
        -wf1,
        wf1[0:1],
        wf1.append(wf2),
    ]:
        assert NormalizeWaveformPython().visit(a_wf) == a_wf

    wf5 = wf4.sample(0.1, wf.Interpolation.Linear)

    times, values = wf5.samples()

    durations = np.diff(times)

    wf6 = piecewise_linear(durations.tolist(), values)

    assert NormalizeWaveformPython().visit(wf5) == wf6

    wf7 = wf4.sample(0.1, wf.Interpolation.Constant)

    times, values = wf5.samples()

    durations = np.diff(times)

    wf8 = piecewise_constant(durations.tolist(), values[:-1])

    assert NormalizeWaveformPython().visit(wf7) == wf8


@patch("bloqade.compiler.codegen.python.waveform.randint")
def test_python_codegen(randint):
    def func_def(wf):
        scan = WaveformScan().scan(wf)
        return CodegenPythonWaveform(scan).emit_func(wf, "test_func")[-1]

    def g(t, a, b):
        return a * np.sin(2 * np.pi * t) + b

    wf1 = wf.Poly([1, 2, 3], 3.0)
    wf2 = wf.Linear(0, 1, 4.0)
    wf3 = wf.Constant(1.0, 4.0)
    wf4 = wf.PythonFn.create(f, 4.0)
    wf5 = wf.PythonFn.create(g, 4.0)

    wf6 = AssignBloqadeIR(dict(a=1, b=2)).emit(wf5)

    randint.side_effect = [0, 1, 2, 3, 4]

    assert (func_def(wf1)) == (
        "def test_func(time):\n"
        "    if time > 3.0:\n"
        "        return 0\n"
        "    __bloqade_var0 = 1 + 2 * (time) ** 1 + 3 * (time) ** 2\n"
        "    return __bloqade_var0"
    )

    assert (func_def(wf2)) == (
        "def test_func(time):\n"
        "    if time > 4.0:\n"
        "        return 0\n"
        "    __bloqade_var0 = 0.25 * (time) + 0\n"
        "    return __bloqade_var0"
    )

    assert (func_def(wf3)) == (
        "def test_func(time):\n"
        "    if time > 4.0:\n"
        "        return 0\n"
        "    __bloqade_var0 = 1.0\n"
        "    return __bloqade_var0"
    )

    assert (func_def(wf4)) == (
        "def test_func(time):\n"
        "    if time > 4.0:\n"
        "        return 0\n"
        "    __bloqade_var0 = __bloqade_waveform_0(time)\n"
        "    return __bloqade_var0"
    )

    assert (func_def(wf6)) == (
        "def test_func(time):\n"
        "    if time > 4.0:\n"
        "        return 0\n"
        "    __bloqade_var0 = __bloqade_waveform_1(time, a = 1, b = 2)\n"
        "    return __bloqade_var0"
    )

    assert (func_def(wf1 + wf2)) == (
        "def test_func(time):\n"
        "    if time > 4.0:\n"
        "        return 0\n"
        "    __bloqade_var1 = 1 + 2 * (time) ** 1 + 3 * (time) ** 2\n"
        "    __bloqade_var2 = 0.25 * (time) + 0\n"
        "    __bloqade_var0 = __bloqade_var1 + __bloqade_var2 if time "
        "< 3.0 else __bloqade_var2\n"
        "    return __bloqade_var0"
    )

    assert (func_def(wf2 + wf1)) == (
        "def test_func(time):\n"
        "    if time > 4.0:\n"
        "        return 0\n"
        "    __bloqade_var1 = 0.25 * (time) + 0\n"
        "    __bloqade_var2 = 1 + 2 * (time) ** 1 + 3 * (time) ** 2\n"
        "    __bloqade_var0 = __bloqade_var1 + __bloqade_var2 if time "
        "< 3.0 else __bloqade_var1\n"
        "    return __bloqade_var0"
    )

    assert (func_def(wf2 + wf3)) == (
        "def test_func(time):\n"
        "    if time > 4.0:\n"
        "        return 0\n"
        "    __bloqade_var1 = 0.25 * (time) + 0\n"
        "    __bloqade_var2 = 1.0\n"
        "    __bloqade_var0 = __bloqade_var1 + __bloqade_var2\n"
        "    return __bloqade_var0"
    )

    assert (func_def(2.0 * wf1)) == (
        "def test_func(time):\n"
        "    if time > 3.0:\n"
        "        return 0\n"
        "    __bloqade_var1 = 1 + 2 * (time) ** 1 + 3 * (time) ** 2\n"
        "    __bloqade_var0 = 2.0 * __bloqade_var1\n"
        "    return __bloqade_var0"
    )

    assert (func_def(-wf1)) == (
        "def test_func(time):\n"
        "    if time > 3.0:\n"
        "        return 0\n"
        "    __bloqade_var1 = 1 + 2 * (time) ** 1 + 3 * (time) ** 2\n"
        "    __bloqade_var0 = -__bloqade_var1\n"
        "    return __bloqade_var0"
    )

    assert (func_def(wf1[1:2])) == (
        "def test_func(time):\n"
        "    if time > 1:\n"
        "        return 0\n"
        "    __bloqade_var1 = 1 + 2 * (time + 1) ** 1 + 3 * (time + 1) ** 2\n"
        "    __bloqade_var0 = __bloqade_var1\n"
        "    return __bloqade_var0"
    )

    assert (func_def(wf1.append(wf2))) == (
        "def test_func(time):\n"
        "    if time > 7.0:\n"
        "        return 0\n"
        "    if time < 3.0:\n"
        "        __bloqade_var1 = 1 + 2 * (time - 0) ** 1 + 3 * (time - 0) ** 2\n"
        "        __bloqade_var0 = __bloqade_var1\n"
        "    elif time <= 7.0:\n"
        "        __bloqade_var2 = 0.25 * (time - 3.0) + 0\n"
        "        __bloqade_var0 = __bloqade_var2\n"
        "    else:\n"
        "        __bloqade_var0 = 0\n"
        "    return __bloqade_var0"
    )

    scan = WaveformScan().scan(wf1)
    func = CodegenPythonWaveform(scan).compile(wf1)

    assert isinstance(func, numba.core.registry.CPUDispatcher)
    assert func.__name__ == "__bloqade_waveform_2"

    scan = WaveformScan().scan(wf1)
    func = CodegenPythonWaveform(scan, jit_compiled=False).compile(wf1)

    assert inspect.isfunction(func)
    assert func.__name__ == "__bloqade_waveform_3"


def test_interpret_vs_python_vs_numba():
    def phase_function(t):
        return np.sin(t)

    def collect_callback(state, metadata, hamiltonian):
        return state.data.copy()

    program = (
        start.add_position([(0, 0), (0, 6)])
        .rydberg.detuning.uniform.piecewise_linear([0.1, 0.8, 0.1], [-10, -10, 20, 20])
        .amplitude.uniform.piecewise_linear([0.1, 0.8, 0.1], [0, 15.7, 15.7, 0])
        .phase.location(0, 1.0)
        .fn(phase_function, 1.0)
        .detuning.scale([0.1, 1.0])
        .piecewise_constant([0.1, 0.3, 0.1], [0, 1, 2])
        .poly([2, -1, 3, -4], 0.5)
    )

    interp_results = program.bloqade.python().run_callback(
        collect_callback, waveform_runtime="interpret"
    )

    python_results = program.bloqade.python().run_callback(
        collect_callback, waveform_runtime="python"
    )

    numba_results = program.bloqade.python().run_callback(
        collect_callback, waveform_runtime="numba"
    )

    for interp_result, python_result, numba_result in zip(
        interp_results, python_results, numba_results
    ):
        assert np.allclose(interp_result, python_result)
        assert np.allclose(interp_result, numba_result)


if __name__ == "__main__":
    test_python_codegen()
