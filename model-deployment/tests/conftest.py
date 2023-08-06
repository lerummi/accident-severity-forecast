import pytest 


@pytest.fixture
def test_model(mocker):  # pylint: disable=missing-function-docstring

    model = mocker.MagicMock()
    model.metadata.to_json.return_value = (
        '{"signature": {"inputs": "[{\\"name\\": \\"input1\\", \
        \\"type\\": \\"integer\\"}, {\\"name\\": \\"input2\\", \
        \\"type\\": \\"string\\"}]"}}'
    )
    model.predict.return_value = [0.]
    return model
