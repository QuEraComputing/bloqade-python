import bloqade.ir as ir

from ..base import Builder, ParamType
from ..coupling import LevelCoupling, Rydberg, Hyperfine
from ..field import Field, Detuning, RabiAmplitude, RabiPhase
from ..spatial import SpatialModulation, Location, Uniform, Var, Scale
from ..waveform import WaveformPrimitive, Slice, Record
from ..parallelize import Parallelize, ParallelizeFlatten

from .stream import BuilderNode

from itertools import repeat
from typing import List, Tuple, Union, Dict


class Parser:
    def __init__(self, ast: Builder) -> None:
        from .stream import BuilderStream

        self.stream = BuilderStream.create(ast)
        self.vector_node_names = []

    def read_address(self) -> Tuple[LevelCoupling, Field, BuilderNode]:
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
        sequence = ir.Sequence({})
        while self.stream.curr is not None:
            coupling_builder, field_builder, spatial_head = self.read_address()

            if coupling_builder is not None:
                # update to new pulse coupling
                coupling_name = coupling_builder.__bloqade_ir__()

            if field_builder is not None:
                # update to new field coupling
                field_name = field_builder.__bloqade_ir__()

            if spatial_head is None:
                break

            pulse = sequence.pulses.get(coupling_name, ir.Pulse({}))
            field = pulse.fields.get(field_name, ir.Field({}))

            new_field = self.read_field(spatial_head)
            field = field.add(new_field)

            pulse.fields[field_name] = field
            sequence.pulses[coupling_name] = pulse

        return sequence

    def read_register(self) -> Union[ir.AtomArrangement, ir.ParallelRegister]:
        # register is always head of the stream
        register_block = self.stream.read()

        register = register_block.node

        parallel_options = self.stream.eat([Parallelize, ParallelizeFlatten])

        if parallel_options is not None:
            parallel_options = parallel_options.node
            return ir.ParallelRegister(register, parallel_options._cluster_spacing)

        return register

    def read_assign(self) -> Dict[str, ParamType]:
        from ..assign import Assign, BatchAssign
        from ..flatten import Flatten

        assign_pragma = self.stream.eat([Assign], [BatchAssign, Flatten])
        if assign_pragma is None:
            return {}

        return assign_pragma.node._assignments

    def read_batch_assign(self) -> List[Dict[str, ParamType]]:
        from ..assign import BatchAssign
        from ..flatten import Flatten

        batch_assign_pragma = self.stream.eat([BatchAssign], [Flatten])

        if batch_assign_pragma is None:
            return [{}]

        assignments = batch_assign_pragma.node._assignments

        tuple_iterators = [
            zip(repeat(name), values) for name, values in assignments.items()
        ]
        return list(map(dict, zip(*tuple_iterators)))

    def read_flatten(self) -> Tuple[str, ...]:
        from ..flatten import Flatten

        flatten_pragma = self.stream.eat([Flatten])
        if flatten_pragma is None:
            return ()
        else:
            order = flatten_pragma.node._order

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

            return order

    def parse(self):
        register = self.read_register()
        sequence = self.read_sequeence()
        static_params = self.read_assign()
        batch_params = self.read_batch_assign()
        order = self.read_flatten()

        return ir.Program(register, sequence, static_params, batch_params, order)
