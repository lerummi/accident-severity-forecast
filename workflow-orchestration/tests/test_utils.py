from logging import Logger
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas
import pytest
from workflows.config import settings
from workflows.utils import (
    download_raw_files,
    fillna_categorical,
    is_numeric_or_datelike,
    load_yaml,
    runcmd,
)

fixtures_dir = Path(__file__).parent / "fixtures"


@pytest.fixture
def example_yaml() -> str:  # pylint: disable=missing-function-docstring
    return "test.yaml"


@pytest.fixture
def test_dataframe_handler() -> Dict[  # pylint: disable=missing-function-docstring
    str, Any
]:
    return {
        "file": "test-dataframe.csv",
        "scope": "test",
        "year": "dataframe",
        "expected": pandas.DataFrame([[1, 2, np.nan]], columns=["a", "b", "c"]),
    }


@pytest.mark.usefixtures("example_yaml")
def test_load_yaml(example_yaml):  # pylint: disable=missing-function-docstring
    result = load_yaml(fixtures_dir / example_yaml)
    expected = eval(result.pop("expected_foo"))  # pylint: disable=eval-used
    assert result == expected


def test_runcmd(example_yaml):  # pylint: disable=missing-function-docstring
    result, error = runcmd(f"ls -l {fixtures_dir}")
    assert example_yaml in result
    assert error == ""


@pytest.mark.parametrize(
    "series, expected",
    [
        (pandas.Series([1, 2, 3]), True),
        (pandas.to_datetime(pandas.Series(["2021-01-01", "2021-01-02"])), True),
        (pandas.Series([pandas.Timedelta(days=1), pandas.Timedelta(days=2)]), True),
        (pandas.Series(["a", "b", "c"]), False),  # Negative test case
    ],
)
def test_is_numeric_or_datelike(
    series, expected
):  # pylint: disable=missing-function-docstring
    assert is_numeric_or_datelike(series) == expected


def test_fillna_categorical():  # pylint: disable=missing-function-docstring
    df = pandas.DataFrame(["a", "b", None], columns=[0])
    df = fillna_categorical(df)
    assert not sum(df.isna())


@pytest.mark.usefixtures("test_dataframe_handler")
def test_download_raw_files(
    monkeypatch, mocker, test_dataframe_handler
):  # pylint: disable=missing-function-docstring

    mocker.patch("workflows.utils.runcmd", return_value=("nothing", "nothing"))
    monkeypatch.setattr(settings, "DATA_DIR", fixtures_dir)

    result = download_raw_files(
        scope=test_dataframe_handler["scope"],
        year=test_dataframe_handler["year"],
        logger=Logger("foo"),
    )

    assert result.equals(test_dataframe_handler["expected"])
