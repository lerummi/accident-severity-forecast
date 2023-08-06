# from workflows.assets import accidents
from pathlib import Path
import pandas

import pytest

from workflows.assets import accidents
from workflows.config import settings

fixtures_dir = Path(__file__).parent / "fixtures"


@pytest.fixture
def raw_accident() -> pandas.DataFrame:  # pylint: disable=missing-function-docstring
    return pandas.read_csv(fixtures_dir / "test_accident.csv", index_col=None)


@pytest.fixture
def raw_vehicle() -> pandas.DataFrame:  # pylint: disable=missing-function-docstring
    return pandas.read_csv(fixtures_dir / "test_vehicle.csv", index_col=None)


@pytest.fixture
def raw_casualty() -> pandas.DataFrame:  # pylint: disable=missing-function-docstring
    return pandas.read_csv(fixtures_dir / "test_casualty.csv", index_col=None)


@pytest.fixture
def accident_vehicle_merged() -> pandas.DataFrame:  # pylint: disable=missing-function-docstring
    return pandas.read_csv(fixtures_dir / "test_accident_vehicle_merged.csv", index_col=None)


@pytest.fixture
def categorical_mapping() -> pandas.DataFrame:  # pylint: disable=missing-function-docstring
    mapping = pandas.read_excel(fixtures_dir / "test_mapping.xlsx", index_col=None)
    mapping["field name"] = mapping["table"].str.lower() + "." + mapping["field name"]
    mapping["code/format"] = mapping["code/format"].astype(str)

    return mapping


@pytest.fixture
def accident_vehicle_casualty_merged() -> pandas.DataFrame:  # pylint: disable=missing-function-docstring
    return pandas.read_csv(
        fixtures_dir / "test_accident_vehicle_casualty_merged.csv",
        index_col=None
    )


@pytest.fixture
def accident_vehicle_casualty_unified() -> pandas.DataFrame:  # pylint: disable=missing-function-docstring
    data = pandas.read_csv(
        fixtures_dir / "test_accident_vehicle_casualty_unified.csv",
        index_col=None
    )
    data["accident.date"] = pandas.to_datetime(data["accident.date"])
    data["accident.time"] = pandas.to_timedelta(data["accident.time"])
    return data


@pytest.fixture
def accident_vehicle_casualty_preprocessed() -> pandas.DataFrame:  # pylint: disable=missing-function-docstring
    data = pandas.read_csv(
        fixtures_dir / "test_accident_vehicle_casualty_preprocessed.csv",
        index_col=None
    )
    #data["accident.date"] = pandas.to_datetime(data["accident.date"])
    #data["accident.time"] = pandas.to_timedelta(data["accident.time"])
    return data



def test_accidents_vehicles_merged(raw_accident, raw_vehicle, accident_vehicle_merged):  # pylint: disable=missing-function-docstring

    merged = accidents.accidents_vehicles_merged(raw_accident, raw_vehicle)
    assert merged.equals(accident_vehicle_merged)


def test_accidents_vehicles_casualties_merged(
        accident_vehicle_merged,
        raw_casualty,
        accident_vehicle_casualty_merged
    ):  # pylint: disable=missing-function-docstring

    merged = accidents.accidents_vehicles_casualties_merged(accident_vehicle_merged, raw_casualty)
    assert merged.equals(accident_vehicle_casualty_merged)


def test_accidents_vehicles_casualties_unify(
        accident_vehicle_casualty_merged,
        categorical_mapping,
        accident_vehicle_casualty_unified
):  # pylint: disable=missing-function-docstring
    
    unified = accidents.accidents_vehicles_casualties_unify(
        accident_vehicle_casualty_merged,
        categorical_mapping
    )

    assert all(  # Looks complicated but pandas.equals does not account for NaN equality
        unified.eq(accident_vehicle_casualty_unified) 
        | (unified.isna() & accident_vehicle_casualty_unified.isna())
    )


def test_accidents_vehicles_casualties_preprocessed(
        monkeypatch,
        accident_vehicle_casualty_unified,
        accident_vehicle_casualty_preprocessed
):  # pylint: disable=missing-function-docstring
    
    monkeypatch.setattr(settings, "CONFIG_DIR", fixtures_dir)
    monkeypatch.setattr(settings, "CATEGORIZATION_BIN_ENDGES", 2)

    print(accident_vehicle_casualty_unified["accident.date"])
    
    preprocessed = accidents.accidents_vehicles_casualties_preprocessed(
        accident_vehicle_casualty_unified
    )

    assert all(  # Looks complicated but pandas.equals does not account for NaN equality
        preprocessed.eq(accident_vehicle_casualty_preprocessed) 
        | (preprocessed.isna() & accident_vehicle_casualty_preprocessed.isna())
    )
