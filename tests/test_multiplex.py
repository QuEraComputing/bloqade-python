from bloqade.lattice import Square
from bloqade.lattice.multiplex import multiplex_lattice
from bloqade.lattice.multiplex_decoder import MultiplexDecoder
from dataclasses import dataclass

# create lattice

lattice = Square(4)

# need to provide capabilities and problem spacing


@dataclass
class Capabilities:
    max_height = 75
    max_width = 75
    num_sites_max = 256


cluster_spacing = 1.0  # 1.0 micrometers

new_lattice, mapping = multiplex_lattice(lattice, Capabilities(), 4.0)

decoder = MultiplexDecoder(mapping=mapping)
