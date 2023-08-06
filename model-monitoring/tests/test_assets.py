from pathlib import Path

import pandas
import pytest
from workflows.assets import (
    recent_accidents_dataset,
    recent_interval_processor,
    reference_accidents_dataset,
)
from workflows.config import settings

fixtures_dir = Path(__file__).parent / "fixtures"


@pytest.fixture
def fake_dataset():  # pylint: disable=missing-function-docstring
    df = pandas.read_csv(fixtures_dir / "test_dataframe.csv")
    df["date"] = pandas.to_datetime(df["date"])
    return df


@pytest.fixture
def fake_recent_interval(  # pylint: disable=missing-function-docstring
    request,
) -> pandas:

    suffix = request.param
    df = pandas.read_csv(fixtures_dir / f"interval_dataframe_{suffix}.csv")
    df["current_date"] = pandas.to_datetime(df["current_date"])
    df["last_processed_date"] = pandas.to_datetime(df["last_processed_date"])
    return df.iloc[0]


def test_reference_accidents_dataset(
    monkeypatch, fake_dataset
):  # pylint: disable=missing-function-docstring

    monkeypatch.setattr(settings, "SIMULATION_START_DATE", "2000-01-10")
    monkeypatch.setattr(settings, "REFERENCE_DATA_SIZE", 5)

    result = reference_accidents_dataset(fake_dataset)

    assert len(result) == 5
    assert "target" not in result


@pytest.mark.parametrize(
    "fake_recent_interval, sim_start, current_sim, expected_output",
    [
        (
            "1",
            "2000-01-01",
            "2000-01-07",
            {
                "last_processed_date": pandas.to_datetime("2000-01-05"),
                "current_date": pandas.to_datetime("2000-01-07"),
            },
        ),
        (
            "1",
            "2000-01-08",
            "2000-01-09",
            {
                "last_processed_date": pandas.to_datetime("2000-01-05"),
                "current_date": pandas.to_datetime("2000-01-09"),
            },
        ),
    ],
    indirect=["fake_recent_interval"],
)
def test_recent_interval_processor(
    mocker, monkeypatch, fake_recent_interval, sim_start, current_sim, expected_output
):  # pylint: disable=missing-function-docstring,too-many-arguments

    monkeypatch.setattr(settings, "SIMULATION_START_DATE", sim_start)
    mocker.patch(
        "workflows.assets.get_simulation_date",
        return_value=pandas.to_datetime(current_sim),
    )
    mocker.patch(
        "workflows.assets.read_pandas_asset", return_value=fake_recent_interval
    )

    result = recent_interval_processor()

    expected = pandas.Series(expected_output)

    assert result.equals(expected)


@pytest.mark.parametrize(
    "fake_recent_interval, output_len, output_min_date, output_max_date",
    [("1", 2, "2000-01-03", "2000-01-04"), ("2", 3, "2000-01-09", "2000-01-11")],
    indirect=["fake_recent_interval"],
)
def test_recent_accidents_dataset(  # pylint: disable=too-many-arguments
    mocker,
    fake_recent_interval,
    output_len,
    output_min_date,
    output_max_date,
    fake_dataset,
):  # pylint: disable=missing-function-docstring

    mocker.patch(
        "workflows.assets.read_pandas_asset", return_value=fake_recent_interval
    )

    X = recent_accidents_dataset(fake_recent_interval, fake_dataset)

    assert len(X) == output_len
    assert X["date"].min() == pandas.to_datetime(output_min_date)
    assert X["date"].max() == pandas.to_datetime(output_max_date)
