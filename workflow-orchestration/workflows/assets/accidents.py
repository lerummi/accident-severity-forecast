import os
import pandas
import numpy as np
from pathlib import Path

from dagster import asset
from dagster import get_dagster_logger

from workflows.utils import (
    runcmd, 
    load_yaml,
    fillna_categorical
)

data_dir = Path(os.environ["DATA_DIR"])
base_url = "https://data.dft.gov.uk/road-accidents-safety-data"
years = range(2016, 2017)

categorization = load_yaml(
    Path(os.environ["CONFIG_DIR"]) / "categorization.yaml"
)


@asset(group_name="downloaded")
def raw_accidents() -> pandas.DataFrame:
    """Download accidents from https://data.dft.gov.uk (from 2016)."""

    logger = get_dagster_logger()

    output_dir = data_dir / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)

    data = []
    for year in years:
        filename = "/".join(
                [
                    base_url,
                    f"dft-road-casualty-statistics-accident-{year}.csv"
                ]
        )

        output_file = output_dir / f"accidents-{year}.csv"

        logger.info(f"Running wget -v {filename} -O {output_file}")
        std_out, std_err = runcmd(f"wget -v {filename} -O {output_file}")
        logger.info(f"StdOut message: {std_out}")
        logger.info(f"StdErr message: {std_err}")

        data.append(
            pandas.read_csv(
                output_file,
                low_memory=False
            )
        )

    return pandas.concat(data, axis=0)


@asset(group_name="downloaded")
def raw_vehicles() -> pandas.DataFrame:
    """Download vehicles from https://data.dft.gov.uk (from 2016)."""

    logger = get_dagster_logger()

    output_dir = data_dir / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)

    data = []
    for year in years:
        filename = "/".join(
                [
                    base_url,
                    f"dft-road-casualty-statistics-vehicle-{year}.csv"
                ]
        )

        output_file = output_dir / f"vehicle-{year}.csv"

        logger.info(f"Running wget -v {filename} -O {output_file}")
        std_out, std_err = runcmd(f"wget -v {filename} -O {output_file}")
        logger.info(f"StdOut message: {std_out}")
        logger.info(f"StdErr message: {std_err}")

        data.append(
            pandas.read_csv(
                output_file,
                low_memory=False
            )
        )

    return pandas.concat(data, axis=0)


@asset(group_name="downloaded")
def raw_casualties() -> pandas.DataFrame:
    """Download casualties from https://data.dft.gov.uk (from 2016)."""

    logger = get_dagster_logger()

    output_dir = data_dir / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)

    data = []
    for year in years:
        filename = "/".join(
                [
                    base_url,
                    f"dft-road-casualty-statistics-casualty-{year}.csv"
                ]
        )

        output_file = output_dir / f"casualty-{year}.csv"

        logger.info(f"Running wget -v {filename} -O {output_file}")
        std_out, std_err = runcmd(f"wget -v {filename} -O {output_file}")
        logger.info(f"StdOut message: {std_out}")
        logger.info(f"StdErr message: {std_err}")

        data.append(
            pandas.read_csv(
                output_file,
                low_memory=False
            )
        )

    return pandas.concat(data, axis=0)


@asset(group_name="merged")
def accidents_vehicles_merged(
    accidents: pandas.DataFrame, 
    vehicles: pandas.DataFrame
    ) -> pandas.DataFrame:
    """
    Merged accidents and vehicles.
    """

    X = accidents.add_prefix("accident.")

    return X.merge(
        vehicles.add_prefix("vehicle."), 
        how="left",
        left_on="accident.accident_index",
        right_on="vehicle.accident_index"
    )

@asset(group_name="merged")
def accidents_vehicles_casualties_merged(
    accidents_vehicles: pandas.DataFrame, 
    casualties: pandas.DataFrame
) -> pandas.DataFrame:
    """
    Merged accidents, vehicles and casualties. Duplicate columns dropped.
    """

    X = accidents_vehicles.merge(
        casualties.add_prefix("casualty."),
        how="left",
        left_on=["vehicle.accident_index", "vehicle.vehicle_reference"],
        right_on=["casualty.accident_index", "casualty.vehicle_reference"]
    )

    # Drop duplicate columns (such with suffix _x, _y)
    drop_columns = list(X.columns[X.columns.str.contains("_x|_y")])
    drop_columns += [
        "vehicle.accident_index", 
        "vehicle.accident_year", 
        "vehicle.accident_reference", 
        "casualty.accident_index", 
        "casualty.accident_year", 
        "casualty.accident_reference"
    ]
    drop_columns.remove("accident.accident_year")
    X.drop(columns=drop_columns, inplace=True)

    return X


@asset(group_name="downloaded")
def categorical_mapping() -> pandas.DataFrame:
    """
    Mapping of id in accident, vehicle and casualty data to labels."""

    logger = get_dagster_logger()

    output_dir = data_dir / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = "/".join(
        [
            base_url, 
            "Road-Safety-Open-Dataset-Data-Guide.xlsx"
        ]
    )
    output_file = output_dir / "mapping.xlsx"

    logger.info(f"Running wget -v {filename} -O {output_file}")
    std_out, std_err = runcmd(f"wget -v {filename} -O {output_file}")
    logger.info(f"StdOut message: {std_out}")
    logger.info(f"StdErr message: {std_err}")

    mapping = pandas.read_excel(output_file)
    mapping["field name"] = (
        mapping["table"].str.lower() + 
        "." + 
        mapping["field name"]
    )

    return mapping


@asset(group_name="normalize_and_clean")
def accidents_vehicles_casualties_unify(
    accidents_vehicles_casualties_ids: pandas.DataFrame,
    mapping: pandas.DataFrame
) -> pandas.DataFrame:
    """
    Replace ids by labels: Combination of accidents, vehicles and casualties.
    Clean and unify missing values to a None values. Apply date(-time)
    conversion of date and time columns.
    """

    logger = get_dagster_logger()

    decode_mapping = {}

    mapping_groupby = (
        mapping
        .dropna(subset="label", how="any")
        .groupby("field name")
        [["code/format", "label"]]
    )

    for field, value in mapping_groupby:
        decode = value.set_index("code/format")["label"].to_dict()

        if -1 not in decode:
            decode[-1] = "Unknown"
        decode_mapping[field] = decode

    # Keep some mapping rules untouched, because label less more informative 
    decode_mapping.pop("accident.first_road_number")
    decode_mapping.pop("accident.second_road_number")
    decode_mapping.pop("accident.speed_limit")

    logger.info(f"Using the following decode_mapping: {decode_mapping}")

    X = accidents_vehicles_casualties_ids
    for k, column in enumerate(X.columns):
        if column in decode_mapping:
            logger.info(f"Decoding column: {column}")
            X[column] = X[column].replace(decode_mapping[column])

    # Based on following pattern, set all matches to None
    pattern = r"(?i)data\s*missing|unknown|undefined"

    # Unify column handling and correct errors
    oor = "Data missing or out of range"
    logger.info(f"Unifying incorrect columns")
    X["accident.speed_limit"].replace(oor, np.nan, inplace=True)
    X["vehicle.age_of_driver"].replace(oor, np.nan, inplace=True)
    X["vehicle.engine_capacity_cc"].replace(oor, np.nan, inplace=True)
    X["casualty.age_of_casualty"].replace(oor, np.nan, inplace=True)
    X["accident.second_road_class"].replace(9, np.nan, inplace=True)
    X["accident.special_conditions_at_site"].replace(0, np.nan, inplace=True)
    X["accident.carriageway_hazards"].replace(0, np.nan, inplace=True)
    X["vehicle.skidding_and_overturning"].replace(0, np.nan, inplace=True)
    X["vehicle.hit_object_in_carriageway"].replace(0, np.nan, inplace=True)
    X["vehicle.hit_object_off_carriageway"].replace(0, np.nan, inplace=True)
    X.replace(-1, np.nan, inplace=True)
    X.replace("-1", np.nan, inplace=True)

    # Regex replace pattern to None
    for column in X:
        logger.info(f"Unifying unknowns in column: {column}")
        X[column] = X[column].replace(
            to_replace=pattern, value=None, regex=True
        )

    # Convert date and time columns to specific pandas objects
    X["accident.time"] = pandas.to_timedelta(X["accident.time"] + ":00")
    X["accident.date"] = pandas.to_datetime(
        X["accident.date"], 
        format="%d/%m/%Y"
    )

    return X


@asset(group_name="normalize_and_clean")
def accidents_vehicles_casualties_dataset(
    accidents_vehicles_casualties_unify: pandas.DataFrame
) -> pandas.DataFrame:
    
    X = accidents_vehicles_casualties_unify
    X = X.set_index("accident.accident_index")

    # Define target, i.e. casualty severity level
    X["target"] = (
        X
        .pop("casualty.casualty_severity")
        .replace(
            {
                np.nan: 0, 
                "Slight": 1, 
                "Serious": 2, 
                "Fatal": 3
            }
        )
    )
    X = X.loc[:, ~X.columns.str.startswith("casualty.")]
    X = X.drop_duplicates()

    n_vehicles = X.groupby(level=0)["vehicle.vehicle_reference"].nunique()
    X["accident.n_vehicles"] = np.nan
    X["accident.n_vehicles"].loc[n_vehicles.index] = n_vehicles.loc[
        n_vehicles.index
    ]

    # Columns in training dataset
    columns = (
        categorization["spatiotemporal_properties"] + 
        categorization["vehicle_properties"] + 
        categorization["environmental_properties"] +
        ["accident.n_vehicles", "target"]
    )
    X = X[columns]

    # Make vehicle columns categorical, so we can multiple vehicle properties
    # one row
    for column in ["vehicle.engine_capacity_cc", "vehicle.age_of_vehicle"]:
        X[column] = pandas.qcut(
            X[column],
            10,
            labels=list(
                map(
                    lambda x: f"{column}#{x}", range(10)
                )
            )
        ).astype(object)

    # Transform data(-time) columns
    X["accident.year"] = X["accident.date"].dt.year
    X["accident.month"] = X["accident.date"].dt.year
    X["accident.weekday"] = X["accident.date"].dt.dayofweek
    X["accident.hour"] = X["accident.time"].dt.total_seconds() / 60 / 60

    X.pop("accident.date")
    X.pop("accident.time")

    X = fillna_categorical(X)

    # Group-agg by accident_index: 
    # Vehicle columns are simply summerized, such that strings (possibly iden-
    # tifying categories) are concatenated
    # Other columns are unique anyway
    # Target column is summarized to mimic a total accident severity score
    vehicle_columns = X.columns[X.columns.str.startswith("vehicle.")]
    other_columns = [
        column for column in X 
        if column not in vehicle_columns and column != "target"
    ]

    agg = {
        **{column: " ".join for column in vehicle_columns},
        **{column: "first" for column in other_columns},
        **{"target": "sum"}
    }

    X = fillna_categorical(X)
    return X.groupby(level=0).agg(agg)
