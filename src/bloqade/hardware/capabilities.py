from dataclasses import dataclass


@dataclass
class Capabilities:
    num_sites_max: int
    max_height: float
    max_width: float
