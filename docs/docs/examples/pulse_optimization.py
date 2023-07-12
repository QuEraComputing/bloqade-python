from bloqade import piecewise_linear, start
from bloqade.ir.location import Square

build =  (
        start.rydberg.rabi.amplitude.uniform.piecewise_linear(
        [0.1, 0.1, 0.1], ["rabi_1", "rabi_2", "rabi_3", "rabi_4"]
        )
    )


def cost_function(x):

    # TODO: Compute time step given by number of descrete points
    # TODO: Variable naming 

    #sequence = (
    #    start.rydberg.rabi.amplitude.uniform.piecewise_linear(
    #    [0.1, 0.1, 0.1], ["rabi_1", "rabi_2", "rabi_3", "rabi_4"]
    #    )
    #)


    build =  (
        start.rydberg.rabi.amplitude.uniform.piecewise_linear(
        [0.1, 0.1, 0.1], ["rabi_1", "rabi_2", "rabi_3", "rabi_4"]
        )
    )


    output = build.assign(rabi_1=x[0], rabi_2=x[1], rabi_3=x[2], rabi_4=x[3]).braket_local_simulator(100).submit().report()

    #result = sequence.assign(args).braket_local_simulator(100).submit()

    # TODO: Post processing to compute the cost function value

    return output

res = cost_function([0.1, 0.1, 0.3, 0.4])
print(res)