import simplejson as json
import os
from bloqade.submission.ir.capabilities import QuEraCapabilities


# TODO: Create unit converter for capabilities
def get_capabilities() -> QuEraCapabilities:
    base_path = os.path.dirname(__file__)
    full_path = os.path.join(base_path, "config", "capabilities.json")
    with open(full_path, "r") as io:
        return QuEraCapabilities(**json.load(io))
