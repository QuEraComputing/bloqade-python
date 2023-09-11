from bloqade.builder.base import Builder
from bloqade.builder.coupling import LevelCoupling, Rydberg, Hyperfine
from bloqade.builder.sequence_builder import SequenceBuilder
from bloqade.builder.field import Field, Detuning, RabiAmplitude, RabiPhase
from bloqade.builder.spatial import SpatialModulation, Location, Uniform, Var, Scale
from bloqade.builder.waveform import WaveformPrimitive, Slice, Record, Sample, Fn
from bloqade.builder.assign import Assign, BatchAssign
from bloqade.builder.flatten import Flatten
from bloqade.builder.parallelize import Parallelize, ParallelizeFlatten
from bloqade.builder.parse.stream import BuilderNode, BuilderStream

import bloqade.ir as ir
from itertools import repeat
from typing import TYPE_CHECKING, Tuple, Union, Dict, List, Optional, Set

if TYPE_CHECKING:
    from bloqade.ir.routine.params import Params, ParamType
    from bloqade.ir.analog_circuit import AnalogCircuit


class Parser:
    stream: Optional["BuilderStream"] = None
    vector_node_names: Set[str] = set()
    sequence: ir.Sequence = ir.Sequence()
    register: Union[ir.AtomArrangement, ir.ParallelRegister, None] = None
    batch_params: List[Dict[str, "ParamType"]] = [{}]
    static_params: Dict[str, "ParamType"] = {}
    order: Tuple[str, ...] = ()

    def reset(self, builder: Builder):
        self.stream = BuilderStream.create(builder)
        self.vector_node_names = set()
        self.sequence = ir.Sequence()
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
        waveform = None
        while curr is not None:
            node = curr.node

            if isinstance(node, Slice):
                waveform = waveform[node._start : node._stop]
            elif isinstance(node, Record):
                waveform = waveform.record(node._name)
            elif isinstance(node, Sample):
                interpolation = node._interpolation
                if interpolation is None:
                    if self.field_name == ir.rabi.phase:
                        interpolation = ir.Interpolation.Constant
                    else:
                        interpolation = ir.Interpolation.Linear
                fn_waveform =  node.__parent__.__bloqade_ir__()
                sample_waveform = ir.Sample(
                    fn_waveform, interpolation, node._dt
                )
                if waveform is None:
                    waveform = sample_waveform
                else:
                    waveform = waveform.append(sample_waveform)
            elif isinstance(node, Fn) and curr.next is not None and isinstance(
                curr.next.node, Sample
            ):
                pass
            elif isinstance(node, WaveformPrimitive):
                if waveform is None:
                    waveform = node.__bloqade_ir__()
                else:
                    waveform = waveform.append(node.__bloqade_ir__())
            else:
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
            node = curr.node

            if isinstance(node, Location):
                scaled_locations[ir.Location(node._label)] = 1.0
            elif isinstance(node, Scale):
                scaled_locations[ir.Location(node.__parent__._label)] = ir.cast(node._value)
            elif isinstance(node, Uniform):
                spatial_modulation = ir.Uniform
            elif isinstance(node, Var):
                spatial_modulation = ir.RunTimeVector(node._name)
                self.vector_node_names.add(node._name)
            else:
                break

            curr = curr.next

        if scaled_locations:
            return scaled_locations, curr
        else:
            return spatial_modulation, curr

    def read_field(self, head) -> ir.Field:
        sm, curr = self.read_spatial_modulation(head)
        wf, _ = self.read_waveform(curr)

        if wf is None or sm is None:
            return ir.Field({})

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
                self.coupling_name = coupling_builder.__bloqade_ir__()

            if field_builder is not None:
                # update to new field coupling
                self.field_name = field_builder.__bloqade_ir__()

            if spatial_head is None:
                break

            pulse = self.sequence.pulses.get(self.coupling_name, ir.Pulse({}))
            field = pulse.fields.get(self.field_name, ir.Field({}))

            new_field = self.read_field(spatial_head)
            field = field.add(new_field)

            pulse.fields[self.field_name] = field
            self.sequence.pulses[self.coupling_name] = pulse

        return self.sequence

    def read_register(self) -> ir.AtomArrangement:
        # register is always head of the stream
        register_node = self.stream.read()
        self.register = register_node.node

        return self.register

    def read_pragmas(self) -> None:
        pragma_types = (
            Assign,
            BatchAssign,
            Flatten,
            Parallelize,
            ParallelizeFlatten,
        )

        stream = self.stream.copy()
        curr = stream.read_next(pragma_types)

        while curr is not None:
            match curr.node:
                case Assign(static_params):
                    self.static_params = {
                        name: value for name, value in static_params.items()
                    }

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
                    flattened_vector_names = order_names.intersection(
                        self.vector_node_names
                    )

                    if flattened_vector_names:
                        raise ValueError(
                            f"Cannot flatten RunTimeVectors: {flattened_vector_names}."
                        )

                case Parallelize(cluster_spacing) | ParallelizeFlatten(cluster_spacing):
                    self.register = ir.ParallelRegister(self.register, cluster_spacing)
                case _:
                    break

            curr = curr.next

    def parse_register(
        self, builder: Builder
    ) -> Union[ir.AtomArrangement, ir.ParallelRegister]:
        self.reset(builder)
        self.read_register()
        self.read_pragmas()
        return self.register

    def parse_sequence(self, builder: Builder) -> ir.Sequence:
        self.reset(builder)
        self.read_sequeence()
        return self.sequence

    def parse_circuit(self, builder: Builder) -> "AnalogCircuit":
        from bloqade.ir.analog_circuit import AnalogCircuit

        self.reset(builder)
        self.read_register()
        self.read_sequeence()
        self.read_pragmas()

        circuit = AnalogCircuit(self.register, self.sequence)

        return circuit

    def parse_source(self, builder: Builder) -> Tuple["AnalogCircuit", "Params"]:
        from bloqade.ir.routine.params import Params
        from bloqade.ir.analog_circuit import AnalogCircuit

        self.reset(builder)
        self.read_register()
        self.read_sequeence()
        self.read_pragmas()

        params = Params(
            static_params=self.static_params,
            batch_params=self.batch_params,
            flatten_params=self.order,
        )
        circuit = AnalogCircuit(self.register, self.sequence)

        return circuit, params
