import json
import os
from quera_ahs_utils.quera_ir.capabilities import QuEraCapabilities


# TODO: Create unit converter for capabilities
def get_capabilities():
    base_path = os.path.dirname(__file__)
    full_path = os.path.join(
        base_path, "quera_api_client", "config", "capabilities.json"
    )
    with open(full_path, "r") as io:
        return QuEraCapabilities(**json.load(io))
