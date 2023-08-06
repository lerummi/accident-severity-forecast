import mlflow
import pytest

from fastapi.testclient import TestClient


@pytest.fixture
def test_app_client(mocker, test_model):  # pylint: disable=missing-function-docstring
    mocker.patch("mlflow.pyfunc.load_model", return_value=test_model)
    from app.main import app
    return TestClient(app)


def test_predict_endpoint(test_app_client):  # pylint: disable=missing-function-docstring

    client = test_app_client

    # Define a sample input data
    data = [{"feature1": 1, "feature2": 2}]

    # Send a POST request to the predict endpoint
    response = client.post("/predict/", json=data)

    # Check that the response has a successful status code
    assert response.status_code == 200

    # Check that the response body contains the expected predictions
    assert "predictions" in response.json()


def test_get_model_info_endpoint(test_app_client):  # pylint: disable=missing-function-docstring
    # Send a GET request to the get_model_info endpoint
    response = test_app_client.get("/info/")

    # Check that the response has a successful status code
    assert response.status_code == 200

    # Check that the response body contains the expected model information
    assert "model_name" in response.json()
    assert "model_version" in response.json()
