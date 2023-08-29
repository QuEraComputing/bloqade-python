import os
import json


def load_config(qpu: str):
    real_path = os.path.realpath(__file__)

    match qpu:
        case "Aquila":
            with open(os.path.join(real_path, "config", "aquila_api_config.json")) as f:
                return json.load(f)
        case "Mock":
            with open(os.path.join(real_path, "config", "mock_api_config.json")) as f:
                return json.load(f)
