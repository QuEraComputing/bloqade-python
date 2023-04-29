import bloqade.ir.waveform as waveform
import bloqade.ir.scalar as scalar

# duration, start, stop
s = waveform.Linear(scalar.Literal(10.0), scalar.Variable("X"), scalar.Literal(5.0))
print(s)  # should show "linear start stop"
s(3.3, X=0.5)  # should resolve properly
s(100.0, X=1.2)  # should return 0 when outside of bounds

s = waveform.Constant(scalar.Literal(5.0), scalar.Variable("Y"))
print(s)
s(0.5, Y=10)
s(5.01, Y=3)  # out of bounds test

s = waveform.Poly(
    scalar.cast([scalar.Literal(1.0), scalar.Literal(2.0), scalar.Literal(3.0)])
)
