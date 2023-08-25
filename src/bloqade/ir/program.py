# from numbers import Real
from typing import TYPE_CHECKING, List, Optional, Union, Dict, Tuple
from bokeh.io import show
from bokeh.layouts import row

if TYPE_CHECKING:
    from bloqade.ir.location.base import AtomArrangement, ParallelRegister
    from bloqade.builder.base import Builder, ParamType
    from bloqade.ir import Sequence
    from numbers import Real

    # from bloqade.task.batch import RemoteBatch


# NOTE: this is just a dummy type bundle geometry and sequence
#       information together and forward them to backends.
class Program:

    """Program is a dummy type that bundle register and sequence together."""

    def __init__(
        self,
        register: Union["AtomArrangement", "ParallelRegister"],
        sequence: "Sequence",
        static_params: Dict[str, "ParamType"] = {},
        batch_params: List[Dict[str, "ParamType"]] = [{}],
        order: Tuple[str, ...] = (),
        builder: Optional["Builder"] = None,
    ):
        self._sequence = sequence
        self._register = register
        self._static_params = static_params
        self._batch_params = batch_params
        # order of flattened parameters
        self._order = order
        self._builder = builder

    @property
    def static_params(self) -> Dict[str, "ParamType"]:
        """Get the instances of variables specified by .assign()

        Returns:
            variable and their instances
        """
        return self._static_params

    @property
    def batch_params(self) -> List[Dict[str, "ParamType"]]:
        """Get the instances of variables specified by .batch_assign()

        Returns:
            batch of variable and their instances
        """
        return self._batch_params

    @property
    def order(self):
        return self._order

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

    @property
    def builder(self):
        """builder objec that is parsed to obtain this program

        Returns:
            Builder: A builder object that is parsed to obtain this program
                See also [`Builder`][bloqade.builder.base.Builder].
        """
        return self._builder

    def parse_args(self, *args) -> Dict[str, "Real"]:
        if len(args) != len(self.order):
            raise ValueError(f"Expected {len(self.order)} arguments, got {len(args)}.")

        return dict(zip(self.order, args))

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
        return row(fig_seq, fig_reg)

    def show(self, **assignments):
        """Interactive visualization of the program

        Args:
            **assignments: assigning the instance value (literal) to the
                existing variables in the program

        """
        show(self.figure(**assignments))


# class BraketService:
#     def __init__(self, program: Program):
#         self.program = program

#     @property
#     def aquila(self) -> "BraketHardware":
#         return BraketHardware(
#             self.program, "arn:aws:braket:us-east-1::device/qpu/quera/Aquila"
#         )

#     @property
#     def local_emulator(self) -> "BraketLocalEmulator":
#         return BraketLocalEmulator(self.program)


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
