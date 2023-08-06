import json
from typing import List

from pydantic import BaseModel, create_model


def type_convert(typestring: str):
    """
    Establish compatibility between types return by MLflow and pydantic.
    """
    if typestring == "string":
        return (str, "string")
    if typestring in ("double", "single"):
        return (float, 0.123)
    if typestring in ("integer", "long"):
        return (int, 0)
    raise ValueError(f"Type '{typestring}' unknown!")


def input_signature_to_schema(model):
    """
    Create pydantic model based on MLflow model signature.
    """
    model_info = json.loads(model.metadata.to_json())
    inputs = eval(model_info["signature"]["inputs"])  # pylint: disable=eval-used
    input_signature = {item["name"]: type_convert(item["type"]) for item in inputs}
    return create_model("ModelInput", **input_signature)


class Predictions(BaseModel):  # pylint: disable=too-few-public-methods
    """
    Predictions model.
    """

    predictions: List[float]
