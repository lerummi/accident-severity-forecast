import pytest
import time
import pandas
from pathlib import Path

from workflows.config import settings
from workflows.utils import get_simulation_date, read_pandas_asset, infer_feature_types

fixtures_dir = Path(__file__).parent / "fixtures"


@pytest.fixture
def dataframe_from_dict(request):
    return pandas.DataFrame(request.param)


@pytest.fixture
def pickled_dataframe():  # pylint: disable=missing-function-docstring
    return "test.pkl"


@pytest.fixture
def pickled_dict():  # pylint: disable=missing-function-docstring
    return "dict.pkl"


class FakeS3Client(object):
    """
    Fake object to minic boto3 S3 client.
    """
    def download_file(*args, **kwargs):
        return


def test_get_simulation_date(monkeypatch):  # pylint: disable=missing-function-docstring

    monkeypatch.setattr(settings, "SIMULATION_START_DATE", "2000-01-01")
    monkeypatch.setattr(settings, "SECONDS_PER_DAY", "1")
    monkeypatch.setattr(settings, "INITIAL_UNIX_TIMESTAMP", "1000000")

    current_timestamp = 1000010

    expected_simulation_date = pandas.to_datetime("2000-01-11")

    assert get_simulation_date(current_timestamp) == expected_simulation_date


def test_read_pandas_asset(monkeypatch, mocker, pickled_dataframe):  # pylint: disable=missing-function-docstring

    monkeypatch.setattr(settings, "WORKFLOW_DATA_BUCKET", fixtures_dir)
    monkeypatch.setattr(settings, "LOCAL_DIR", fixtures_dir)
    mocker.patch("boto3.client", return_value=FakeS3Client())

    result = read_pandas_asset(pickled_dataframe)

    assert isinstance(result, pandas.DataFrame)


def test_read_no_pandas_asset(monkeypatch, mocker, pickled_dict):  # pylint: disable=missing-function-docstring

    monkeypatch.setattr(settings, "WORKFLOW_DATA_BUCKET", fixtures_dir)
    monkeypatch.setattr(settings, "LOCAL_DIR", fixtures_dir)


    mocker.patch("boto3.client", return_value=FakeS3Client())

    with pytest.raises(ImportError):
        read_pandas_asset(pickled_dict)


@pytest.mark.parametrize(
        "dataframe_from_dict, expected_outputs, skip, max_categorical_nunique",
        [
            (
                {"A": [1, 2, 3], "B": [4, 5, 6], "C": [7, 8, 9]},
                {"categorical": [], "text": [], "numerical": ["A", "B", "C"]},
                None,
                10
            ),
            (
                {"A": ["a", "b", "c"], "B": ["d", "e", "f"], "C": ["g", "h", "i"]},
                {"categorical": ["A", "B", "C"], "text": [], "numerical": []},
                None,
                10
            ),
            (
                {"A": [1, 2, 3], "B": ["d", "e", "f"], "C": ["g", "h", "i"]},
                {"categorical": ["B", "C"], "text": [], "numerical": ["A"]},
                None,
                10
            ),
            (
                {"A": [1, 2, 3], "B": ["d", "e", "f"], "C": ["g", "h", "i"]},
                {"categorical": ["B", "C"], "text": [], "numerical": []},
                ["A"],
                10
            ),
            (
                {"A": ["a", "a", "a"], "B": ["d", "e", "f"], "C": ["g", "h", "i"]},
                {"categorical": ["A"], "text": ["B", "C"], "numerical": []},
                None,
                2
            )
        ],
        indirect=["dataframe_from_dict"]
)
def test_infer_feature_types(dataframe_from_dict, expected_outputs, skip, max_categorical_nunique):  # pylint: disable=missing-function-docstring

    assert infer_feature_types(
        dataframe_from_dict, 
        skip, 
        max_categorical_nunique
    ) == expected_outputs
