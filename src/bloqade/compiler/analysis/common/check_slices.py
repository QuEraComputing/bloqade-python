from bloqade.ir.visitor import BloqadeIRVisitor
from bloqade.ir.control import waveform, pulse, sequence
from beartype.typing import Union


class CheckSlices(BloqadeIRVisitor):
    def check_slice(self, node: Union[waveform.Slice, pulse.Slice, sequence.Slice]):
        start_time = node.start()
        stop_time = node.stop()

        duration = node.waveform.duration()

        if start_time < 0:
            raise ValueError(f"Start time {start_time} is negative")

        if stop_time < 0:
            raise ValueError(f"Stop time {stop_time} is negative")

        if start_time > stop_time:
            raise ValueError(
                f"Start time {start_time} is greater than stop time {stop_time}"
            )

        if stop_time > duration:
            raise ValueError(
                f"Stop time {stop_time} is greater than waveform duration {duration}"
            )

    def visit_waveform_Slice(self, node: waveform.Slice):
        self.visit(node.waveform)
        self.check_slice(node)

    def visit_pulse_Slice(self, node: pulse.Slice):
        self.visit(node.pulse)
        self.check_slice(node)

    def visit_sequence_Slice(self, node: sequence.Slice):
        self.visit(node.sequence)
        self.check_slice(node)
