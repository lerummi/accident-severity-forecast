import json
from typing import Dict, List

from pydantic import BaseModel, create_model


def type_convert(typestring: str):
    if typestring == "string":
        return (str, "string")
    elif typestring in ("double", "single"):
        return (float, 0.123)
    elif typestring in ("integer", "long"):
        return (int, 0)
    else:
        raise ValueError(f"Type '{typestring}' unknown!")


def input_signature_to_schema(model):
    model_info = json.loads(model.metadata.to_json())
    inputs = eval(model_info["signature"]["inputs"])
    input_signature = {item["name"]: type_convert(item["type"]) for item in inputs}
    return create_model("ModelInput", **input_signature)


class Predictions(BaseModel):
    predictions: List[float]
