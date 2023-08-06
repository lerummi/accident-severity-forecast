import pytest

from workflows.models import type_convert, input_signature_to_schema


@pytest.mark.parametrize(
        "inputs, expected_outputs",
        [
            ("string", str),
            ("double", float),
            ("long", int)
        ]
)
def test_type_convert(inputs, expected_outputs):  # pylint: disable=missing-function-docstring

    result = type_convert(inputs)
    assert result[0] == expected_outputs


def test_input_signature_to_schema(test_model):  # pylint: disable=missing-function-docstring

    schema = input_signature_to_schema(test_model).model_json_schema()
    properties = schema["properties"]
    assert "input1" in properties
    assert "input2" in properties
    assert properties["input1"]["type"] == "integer"
    assert properties["input2"]["type"] == "string"
