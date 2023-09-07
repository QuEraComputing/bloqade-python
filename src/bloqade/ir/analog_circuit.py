# from numbers import Real
from typing import TYPE_CHECKING, Union
from bloqade.visualization import display_ir

if TYPE_CHECKING:
    from bloqade.ir.location.base import AtomArrangement, ParallelRegister
    from bloqade.ir import Sequence


# NOTE: this is just a dummy type bundle geometry and sequence
#       information together and forward them to backends.
class AnalogCircuit:

    """Program is a dummy type that bundle register and sequence together."""

    def __init__(
        self,
        register: Union["AtomArrangement", "ParallelRegister"],
        sequence: "Sequence",
    ):
        self._sequence = sequence
        self._register = register

    @property
    def register(self):
        """Get the register of the program.

        Returns:
            register (Union["AtomArrangement", "ParallelRegister"])

        Note:
            If the program is built with
            [`parallelize()`][bloqade.builder.emit.Emit.parallelize],
            The the register will be a
            [`ParallelRegister`][bloqade.ir.location.base.ParallelRegister].
            Otherwise it will be a
            [`AtomArrangement`][bloqade.ir.location.base.AtomArrangement].
        """
        return self._register

    @property
    def sequence(self):
        """Get the sequence of the program.


        Returns:
            Sequence: the sequence of the program.
                See also [`Sequence`][bloqade.ir.control.sequence.Sequence].

        """
        return self._sequence

    def __eq__(self, other):
        if isinstance(other, AnalogCircuit):
            return (self.register == other.register) and (
                self.sequence == other.sequence
            )

        return False

    def __repr__(self):
        # TODO: add repr for static_params, batch_params and order
        out = ""
        if self._register is not None:
            out += self._register.__repr__()

        out += "\n"

        if self._sequence is not None:
            out += self._sequence.__repr__()

        return out

    def figure(self, **assignments):
        fig_reg = self._register.figure(**assignments)
        fig_seq = self._sequence.figure(**assignments)
        return fig_seq, fig_reg

    def show(self, **assignments):
        """Interactive visualization of the program

        Args:
            **assignments: assigning the instance value (literal) to the
                existing variables in the program

        """
        display_ir(self, assignments)


# class BraketService:
#     def __init__(self, batch: Batch):
#         self.batch = batch

#     @property
#     def aquila(self) -> "BraketHardware":
#         return BraketHardware(
#             self.batch, "arn:aws:braket:us-east-1::device/qpu/quera/Aquila"
#         )

#     @property
#     def local_emulator(self) -> "BraketLocalEmulator":
#         return BraketLocalEmulator(self.batch)


# class BraketHardware:
#     def __init__(self, program: Program, device_arn: str):
#         self.program = program
#         self.device_arn = device_arn

#     def _compile_batch(
#         self, shots: int, args: Tuple[Real, ...], name: Optional[str] = None
#     ) -> "RemoteBatch":
#         from bloqade.compile.braket import BraketBatchCompiler
#         from bloqade.submission.braket import BraketBackend

#         backend = BraketBackend(
#             device_arn=self.device_arn,
#         )

#         return BraketBatchCompiler(
#             program=self.program,
#             backend=backend,
#         ).compile(shots, args, name=name)

#     def submit(
#         self, shots: int, args: Tuple[Real, ...], name: Optional[str] = None
#     ) -> "RemoteBatch":
#         batch = self._compile_batch(shots, args, name=name)
#         batch._submit()

#         return batch

#     def run(
#         self,
#         shots: int,
#         args: Tuple[Real, ...],
#         name: Optional[str] = None,
#         shuffle_submit_order: bool = False,
#     ) -> "RemoteBatch":
#         batch = self._compile_batch(shots, args, name=name)
#         batch._submit(shuffle_submit_order=shuffle_submit_order)
#         batch.pull()

#         return batch

#     def __call__(self, *args, shots: int = 1):
#         return self.run(shots, args)
