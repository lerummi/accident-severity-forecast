import pytest
import pandas
from pathlib import Path
import boto3


from workflows.helpers.utils import (
    load_yaml, 
    infer_catboost_feature_types, 
    read_partitioned_pandas_asset
)
from workflows.config import settings


fixtures_dir = Path(__file__).parent / "fixtures"


class FakeS3Client(object):
    """
    Fake object to minic boto3 S3 client.
    """
    def download_file(*args, **kwargs):
        return


@pytest.fixture
def yaml_file(tmp_path):  # pylint: disable=missing-function-docstring
    yaml_data = """
    key1: value1
    key2: value2
    """
    file_path = tmp_path / "test.yaml"
    file_path.write_text(yaml_data)
    return file_path


@pytest.fixture
def pickled_dataframe():  # pylint: disable=missing-function-docstring
    return "test.pkl"


@pytest.fixture
def pickled_dict():  # pylint: disable=missing-function-docstring
    return "dict.pkl"


def test_load_yaml(yaml_file):  # pylint: disable=missing-function-docstring
    expected_result = {"key1": "value1", "key2": "value2"}
    result = load_yaml(yaml_file)
    assert result == expected_result


def test_infer_catboost_feature_types():  # pylint: disable=missing-function-docstring
    data = pandas.DataFrame({
        "col1": ["a", "a", "b"],
        "col2": [1, 2, 3],
        "col3": ["x", "y", "z"]
    })

    expected_result = {
        "categorical": ["col1"],
        "text": ["col3"]
    }

    result = infer_catboost_feature_types(data, max_categorical_nunique=2)
    assert result == expected_result


def test_read_partitioned_pandas_asset(monkeypatch, mocker, pickled_dataframe):  # pylint: disable=missing-function-docstring

    monkeypatch.setattr(settings, "WORKFLOW_DATA_BUCKET", fixtures_dir)
    monkeypatch.setattr(settings, "LOCAL_FOLDER", fixtures_dir)

    mocker.patch("boto3.client", return_value=FakeS3Client())

    result = read_partitioned_pandas_asset(pickled_dataframe)

    assert isinstance(result, pandas.DataFrame)


def test_read_partitioned_no_pandas_asset(monkeypatch, mocker, pickled_dict):  # pylint: disable=missing-function-docstring

    monkeypatch.setattr(settings, "WORKFLOW_DATA_BUCKET", fixtures_dir)
    monkeypatch.setattr(settings, "LOCAL_FOLDER", fixtures_dir)

    mocker.patch("boto3.client", return_value=FakeS3Client())

    with pytest.raises(ImportError):
        read_partitioned_pandas_asset(pickled_dict)
