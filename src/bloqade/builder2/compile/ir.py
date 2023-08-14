from typing import Tuple, Union, TYPE_CHECKING

from ..base import Builder

from ..coupling import LevelCoupling, Rydberg, Hyperfine
from ..field import Field, Detuning, RabiAmplitude, RabiPhase
from ..spatial import SpatialModulation, Location, Uniform, Var, Scale
from ..waveform import (
    WaveformPrimitive,
    Slice,
    Record,
)
from ..parallelize import Parallelize, ParallelizeFlatten

if TYPE_CHECKING:
    from bloqade.ir import Waveform as ir_Waveform
    from bloqade.ir import SpatialModulation as ir_SpatialModulation
    from bloqade.ir import Field as ir_Field
    from bloqade.ir import Sequence as ir_Sequence
    from bloqade.ir import ParallelRegister as ir_ParallelRegister
    from bloqade.ir import AtomArrangement as ir_AtomArrangement
    from .stream import BuilderNode


class BuilderCompiler:
    def __init__(self, ast: Builder) -> None:
        from .stream import BuilderStream

        self.stream = BuilderStream.create(ast)


class SequenceCompiler(BuilderCompiler):
    def read_address(self) -> Tuple[LevelCoupling, Field, "BuilderNode"]:
        spatial = self.stream.eat([Location, Uniform, Var], [Scale])
        curr = spatial

        if curr is None:
            return (None, None, None)

        while curr.next is not None:
            if not isinstance(curr.node, SpatialModulation):
                break
            curr = curr.next

        if type(spatial.node.__parent__) in [Detuning, RabiAmplitude, RabiPhase]:
            field = spatial.node.__parent__  # field is updated
            if type(field) in [RabiAmplitude, RabiPhase]:
                coupling = field.__parent__.__parent__  # skip Rabi
            else:
                coupling = field.__parent__

            # coupling not updated
            if type(coupling) not in [Rydberg, Hyperfine]:
                coupling = None
            return (coupling, field, spatial)
        else:  # only spatial is updated
            return (None, None, spatial)

    def read_waveform(self, head: "BuilderNode") -> Tuple["ir_Waveform", "BuilderNode"]:
        curr = head
        waveform = head.node.__bloqade_ir__()
        curr = curr.next
        while curr is not None:
            match curr.node:
                case WaveformPrimitive() as wf:
                    waveform = waveform.append(wf.__bloqade_ir__())
                case Slice(start, stop, _):
                    waveform = waveform[start:stop]
                case Record(name, _):
                    waveform = waveform.record(name)
                case _:
                    break
            curr = curr.next
        return waveform, curr

    def read_spatial_modulation(
        self, head: "BuilderNode"
    ) -> Tuple["ir_SpatialModulation", "BuilderNode"]:
        import bloqade.ir as ir

        curr = head
        spatial_modulation = None
        scaled_locations = ir.ScaledLocations({})

        while curr is not None:
            match curr.node:
                case Location(label, _):
                    scaled_locations[ir.Location(label)] = 1.0
                case Scale(value, Location(label, _)):
                    scaled_locations[ir.Location(label)] = ir.cast(value)
                case Uniform(_):
                    spatial_modulation = ir.Uniform
                case Var(name, _):
                    spatial_modulation = ir.RunTimeVector(name)
                case _:
                    break
            curr = curr.next

        if scaled_locations:
            return scaled_locations, curr
        else:
            return spatial_modulation, curr

    def read_field(self, head) -> "ir_Field":
        from bloqade.ir import Field

        sm, curr = self.read_spatial_modulation(head)
        wf, _ = self.read_waveform(curr)
        return Field({sm: wf})

    def compile(self) -> "ir_Sequence":
        from bloqade.ir import Sequence, Pulse, Field

        coupling_builder, field_builder, spatial_head = self.read_address()

        sequence = Sequence({})
        coupling_name = coupling_builder.__bloqade_ir__()
        field_name = field_builder.__bloqade_ir__()

        pulse = sequence.pulses.get(coupling_name, Pulse({}))
        field = pulse.fields.get(field_name, Field({}))

        new_field = self.read_field(spatial_head)
        field = field.add(new_field)

        while True:
            coupling_builder, field_builder, spatial_head = self.read_address()

            if coupling_builder is not None:
                # update old pulse
                sequence.pulses[coupling_name] = pulse
                # create/access new pulse
                coupling_name = coupling_builder.__bloqade_ir__()
                pulse = sequence.pulses.get(coupling_name, Pulse({}))

            if field_builder is not None:
                # update old field
                pulse.fields[field_name] = field
                # create/access new field
                field_name = field_builder.__bloqade_ir__()
                field = pulse.fields.get(field_name, Field({}))

            if spatial_head is None:
                break

            new_field = self.read_field(spatial_head)
            field = field.add(new_field)

        return sequence


class RegisterCompiler(BuilderCompiler):
    def compile(self) -> Union["ir_AtomArrangement", "ir_ParallelRegister"]:
        from bloqade.ir import ParallelRegister

        # register is always head of the stream
        register_block = self.stream.read()

        register = register_block.node

        parallel_options = self.stream.eat([Parallelize, ParallelizeFlatten])

        if parallel_options is not None:
            parallel_options = parallel_options.node
            return ParallelRegister(register, parallel_options._cluster_spacing)

        return register
