import bloqade.lattice as lattice
from bloqade.ir import Sequence, rydberg, detuning, rabi, Uniform, Linear, Constant

lattice.Square(6).rydberg.detuning.uniform.apply(
    Constant("initial_detuning", "up_time")
    .append(Linear("initial_detuning", "final_detuning", "anneal_time"))
    .append(Constant("final_detuning", "up_time"))
).rabi.amplitude.uniform.apply(
    Linear(0.0, "rabi_amplitude_max", "up_time")
    .append(Constant("rabi_amplitude_max", "anneal_time"))
    .append(Linear("rabi_amplitude_max", 0.0, "up_time"))
).braket(
    nshots=1000
).submit(
    token="112312312"
).report()


# dict interface

seq = Sequence(
    {
        rydberg: {
            detuning: {
                Uniform: Constant("initial_detuning", "up_time")
                .append(Linear("initial_detuning", "final_detuning", "anneal_time"))
                .append(Constant("final_detuning", "up_time")),
            },
            rabi.amplitude: {
                Uniform: Linear(0.0, "rabi_amplitude_max", "up_time")
                .append(Constant("rabi_amplitude_max", "anneal_time"))
                .append(Linear("rabi_amplitude_max", 0.0, "up_time"))
            },
        }
    }
)

lattice.Square(6).apply(seq).braket(nshots=1000).submit(token="112312312").report()

print(seq)
