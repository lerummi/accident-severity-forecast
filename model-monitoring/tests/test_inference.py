import pandas
import pytest
import requests

from workflows.inference import make_prediction
from workflows.config import settings


@pytest.fixture
def sample_data():  # pylint: disable=missing-function-docstring
    data = {
        "accident.accident_index": [1, 2, 3],
        "date": ["2021-01-01", "2021-01-02", "2021-01-03"],
        "feature1": [0.5, 0.6, 0.7],
        "feature2": [0.8, 0.9, 1.0],
        "target": [1, 0, 1]
    }
    return pandas.DataFrame(data)


def test_make_prediction(mocker, sample_data):  # pylint: disable=missing-function-docstring
    # Mock the requests.post function
    mock_post = mocker.patch("requests.post")
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "predictions": [0.9, 0.1, 0.8]
    }

    # Call the make_prediction function
    result = make_prediction(sample_data)

    # Assert that the POST request was made with the correct data
    mock_post.assert_called_once()

    # Get the arguments passed to the POST request
    args, kwargs = mock_post.call_args
    url = args[0]
    data = kwargs["json"]

    assert url == settings.PREDICT_URL
    assert data == [
        {'feature1': 0.5, 'feature2': 0.8, 'target': 1}, 
        {'feature1': 0.6, 'feature2': 0.9, 'target': 0}, 
        {'feature1': 0.7, 'feature2': 1.0, 'target': 1}
    ]

    # Assert that the result DataFrame has the correct columns and values
    expected_result = pandas.DataFrame(
        {
            "predictions": [0.9, 0.1, 0.8],
            "date": ["2021-01-01", "2021-01-02", "2021-01-03"]
        }, 
        index=[1, 2, 3]
    )
    expected_result.index.name = "accident.accident_index"

    pandas.testing.assert_frame_equal(result, expected_result)
