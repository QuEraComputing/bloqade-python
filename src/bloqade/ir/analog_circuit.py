# from numbers import Real
from bloqade.visualization import (
    display_ir,
    get_atom_arrangement_figure,
    assemble_atom_arrangement_panel,
)
from bloqade.ir.control.sequence import SequenceExpr
from bloqade.ir.location.location import AtomArrangement, ParallelRegister
from bloqade.ir.tree_print import Printer
from beartype.typing import Union, List, Tuple, Dict
from pydantic.v1.dataclasses import dataclass
import pandas as pd


# NOTE: this is just a dummy type bundle geometry and sequence
#       information together and forward them to backends.
@dataclass(frozen=True)
class AnalogCircuit:
    """AnalogCircuit is a dummy type that bundle register and sequence together."""

    atom_arrangement: Union[ParallelRegister, AtomArrangement]
    sequence: SequenceExpr

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
        return self.atom_arrangement

    def __eq__(self, other):
        if isinstance(other, AnalogCircuit):
            return (self.register == other.register) and (
                self.sequence == other.sequence
            )

        return False

    def __str__(self):
        out = ""
        if self.register is not None:
            out += self.register.__str__()

        out += "\n"

        if self.sequence is not None:
            out += self.sequence.__str__()

        return out

    def print_node(self):
        return "AnalogCircuit"

    def children(self):
        return {"register": self.atom_arrangement, "sequence": self.sequence}

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)

    def figure(self, **assignments):
        fig_regs = []
        fig_keys = []

        fig_reg = self.register.figure(**assignments)
        fig_seq = self.sequence.figure(**assignments)

        fig_regs.append(fig_reg)
        fig_keys.append("Filling")

        # extract channel info from fig_seq, and
        # analysis the SpatialModulation information
        spmod_extracted_data: Dict[str, Tuple[List[int], List[float]]] = {}

        for tab in fig_seq.tabs:
            pulse_name = tab.title
            field_plots = tab.child.children
            for field in field_plots:
                # extract SpMod:
                field_name = field.children[0].text.strip()
                spmod = field.children[1].children[0]

                Spmod_raw_data = pd.DataFrame(spmod.source.data)

                # exclude uniform
                Spmod_raw_data = Spmod_raw_data[Spmod_raw_data.d1 != "uni"]

                channels = Spmod_raw_data.d0.unique()
                if len(channels) == 0:
                    continue

                for ch in channels:
                    ch_data = Spmod_raw_data[Spmod_raw_data.d0 == ch]

                    sites = list(
                        map(lambda x: int(x.split("[")[-1].split("]")[0]), ch_data.d1)
                    )
                    values = list(ch_data.px.astype(float))

                    key = f"{pulse_name}.{field_name}.{ch}"
                    spmod_extracted_data[key] = (sites, values)

        for key, colors in spmod_extracted_data.items():
            fig_reg = get_atom_arrangement_figure(self.register, colors, **assignments)
            fig_reg.visible = False
            fig_regs.append(fig_reg)
            fig_keys.append(key)

        return fig_seq, assemble_atom_arrangement_panel(fig_regs, fig_keys)

    def show(self, **assignments):
        """Interactive visualization of the program

        Args:
            **assignments: assigning the instance value (literal) to the
                existing variables in the program

        """
        display_ir(self, assignments)
