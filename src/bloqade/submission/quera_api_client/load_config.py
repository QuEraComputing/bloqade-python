import os
import json


def load_config(qpu: str):
    real_path = os.path.realpath(__file__)
    real_path_list = os.path.split(real_path)[:-1]
    real_path = os.path.join(*real_path_list)

    match qpu:
        case "Aquila":
            with open(
                os.path.join(real_path, "config", "aquila_api_config.json"), "r"
            ) as f:
                return json.load(f)
        case "Mock":
            with open(
                os.path.join(real_path, "config", "mock_api_config.json"), "r"
            ) as f:
                return json.load(f)
