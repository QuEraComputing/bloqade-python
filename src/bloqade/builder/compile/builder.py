import bloqade.ir as ir

from ..base import Builder
from ..coupling import LevelCoupling, Rydberg, Hyperfine
from ..sequence_builder import SequenceBuilder
from ..field import Field, Detuning, RabiAmplitude, RabiPhase
from ..spatial import SpatialModulation, Location, Uniform, Var, Scale
from ..waveform import WaveformPrimitive, Slice, Record
from ..assign import Assign, BatchAssign
from ..flatten import Flatten
from ..parallelize import Parallelize, ParallelizeFlatten

from .stream import BuilderNode

from itertools import repeat
from typing import Tuple


class Parser:
    pragma_types = (
        Assign,
        BatchAssign,
        Flatten,
        Parallelize,
        ParallelizeFlatten,
    )

    def __init__(self, ast: Builder) -> None:
        from .stream import BuilderStream

        self.stream = BuilderStream.create(ast)
        self.vector_node_names = []
        self.sequence = ir.Sequence({})
        self.register = None
        self.batch_params = [{}]
        self.static_params = {}
        self.order = ()

    def read_address(self, stream) -> Tuple[LevelCoupling, Field, BuilderNode]:
        spatial = stream.eat([Location, Uniform, Var], [Scale])
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

    def read_waveform(self, head: BuilderNode) -> Tuple[ir.Waveform, BuilderNode]:
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
        self, head: BuilderNode
    ) -> Tuple[ir.SpatialModulation, BuilderNode]:
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
                    self.vector_node_names.append(name)
                case _:
                    break
            curr = curr.next

        if scaled_locations:
            return scaled_locations, curr
        else:
            return spatial_modulation, curr

    def read_field(self, head) -> ir.Field:
        sm, curr = self.read_spatial_modulation(head)
        wf, _ = self.read_waveform(curr)
        return ir.Field({sm: wf})

    def read_sequeence(self) -> ir.Sequence:
        if isinstance(self.stream.curr.node, SequenceBuilder):
            # case with sequence builder object.
            self.sequence = self.stream.read().node.sequence
            return self.sequence

        stream = self.stream.copy()
        while stream.curr is not None:
            coupling_builder, field_builder, spatial_head = self.read_address(stream)
            if coupling_builder is not None:
                # update to new pulse coupling
                coupling_name = coupling_builder.__bloqade_ir__()

            if field_builder is not None:
                # update to new field coupling
                field_name = field_builder.__bloqade_ir__()

            if spatial_head is None:
                break

            pulse = self.sequence.pulses.get(coupling_name, ir.Pulse({}))
            field = pulse.fields.get(field_name, ir.Field({}))

            new_field = self.read_field(spatial_head)
            field = field.add(new_field)

            pulse.fields[field_name] = field
            self.sequence.pulses[coupling_name] = pulse

        return self.sequence

    def read_register(self) -> ir.AtomArrangement:
        # register is always head of the stream
        register_node = self.stream.read()
        self.register = register_node.node

        return self.register

    def read_pragmas(self) -> None:
        stream = self.stream.copy()
        curr = stream.read_next(Parser.pragma_types)

        while curr is not None:
            match curr.node:
                case Assign(static_params):
                    self.static_params = static_params
                case BatchAssign(batch_param):
                    tuple_iterators = [
                        zip(repeat(name), values)
                        for name, values in batch_param.items()
                    ]
                    self.batch_params = list(map(dict, zip(*tuple_iterators)))
                case Flatten(order):
                    self.order = order

                    seen = set()
                    dup = []
                    for x in order:
                        if x not in seen:
                            seen.add(x)
                        else:
                            dup.append(x)

                    if dup:
                        raise ValueError(f"Cannot flatten duplicate names {dup}.")

                    order_names = set([*order])
                    flattened_vector_names = order_names.intersection(order_names)

                    if flattened_vector_names:
                        raise ValueError(
                            f"Cannot flatten RunTimeVectors: {flattened_vector_names}."
                        )

                case Parallelize(cluster_spacing) | ParallelizeFlatten(cluster_spacing):
                    self.register = ir.ParallelRegister(self.register, cluster_spacing)
                case _:
                    break

            curr = curr.next

    def parse(self):
        self.read_register()
        self.read_sequeence()
        self.read_pragmas()
        return ir.Program(
            self.register,
            self.sequence,
            self.static_params,
            self.batch_params,
            self.order,
        )
