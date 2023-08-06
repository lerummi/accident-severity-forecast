import os
from pathlib import Path
from typing import Dict

import numpy as np
import pandas
from dagster import StaticPartitionsDefinition, asset, get_dagster_logger
from workflows.config import settings
from workflows.utils import download_raw_files, fillna_categorical, load_yaml, runcmd

years = settings.YEARS_TO_PROCESS


@asset(
    partitions_def=StaticPartitionsDefinition(years),
    group_name="1_download_source_datasets",
    io_manager_key="s3_io_manager",
)
def raw_accidents(context) -> pandas.DataFrame:
    """Download accidents from data.dft.gov.uk (starting 2016)."""

    logger = get_dagster_logger()
    year = context.asset_partition_key_for_output()

    return download_raw_files("accident", year, logger)


@asset(
    partitions_def=StaticPartitionsDefinition(years),
    group_name="1_download_source_datasets",
    io_manager_key="s3_io_manager",
)
def raw_vehicles(context) -> pandas.DataFrame:
    """Download accidents from data.dft.gov.uk (starting 2016)."""

    logger = get_dagster_logger()
    year = context.asset_partition_key_for_output()

    return download_raw_files("vehicle", year, logger)


@asset(
    partitions_def=StaticPartitionsDefinition(years),
    group_name="1_download_source_datasets",
    io_manager_key="s3_io_manager",
)
def raw_casualties(context) -> pandas.DataFrame:
    """Download accidents from data.dft.gov.uk (starting 2016)."""

    logger = get_dagster_logger()
    year = context.asset_partition_key_for_output()

    return download_raw_files("casualty", year, logger)


@asset(
    partitions_def=StaticPartitionsDefinition(years),
    group_name="2_merge_downloaded_datasets",
    io_manager_key="s3_io_manager",
    compute_kind="pandas",
)
def accidents_vehicles_merged(
    raw_accidents: pandas.DataFrame, raw_vehicles: pandas.DataFrame
) -> pandas.DataFrame:
    """
    Merged accidents and vehicles.
    """

    X = raw_accidents.add_prefix("accident.")

    return X.merge(
        raw_vehicles.add_prefix("vehicle."),
        how="left",
        left_on="accident.accident_index",
        right_on="vehicle.accident_index",
    )


@asset(
    partitions_def=StaticPartitionsDefinition(years),
    group_name="2_merge_downloaded_datasets",
    io_manager_key="s3_io_manager",
    compute_kind="pandas",
)
def accidents_vehicles_casualties_merged(
    accidents_vehicles_merged: pandas.DataFrame,
    raw_casualties: pandas.DataFrame,
) -> pandas.DataFrame:
    """
    Merged accidents, vehicles and casualties. Duplicate columns dropped.
    """

    X = accidents_vehicles_merged.merge(
        raw_casualties.add_prefix("casualty."),
        how="left",
        left_on=["vehicle.accident_index", "vehicle.vehicle_reference"],
        right_on=["casualty.accident_index", "casualty.vehicle_reference"],
    )

    # Drop duplicate columns (such with suffix _x, _y)
    drop_columns = list(X.columns[X.columns.str.contains("_x|_y")])
    drop_columns += [
        "vehicle.accident_index",
        "vehicle.accident_year",
        "vehicle.accident_reference",
        "casualty.accident_index",
        "casualty.accident_year",
        "casualty.accident_reference",
    ]
    drop_columns.remove("accident.accident_year")
    X.drop(columns=drop_columns, inplace=True)

    return X


@asset(group_name="1_download_source_datasets", io_manager_key="s3_io_manager")
def categorical_mapping() -> pandas.DataFrame:
    """
    Mapping of id in accident, vehicle and casualty data to labels."""

    logger = get_dagster_logger()

    output_dir = Path(settings.DATA_DIR) / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = "/".join([settings.BASE_URL, "Road-Safety-Open-Dataset-Data-Guide.xlsx"])
    output_file = output_dir / "mapping.xlsx"

    logger.info(f"Running wget -v {filename} -O {output_file}")
    std_out, std_err = runcmd(f"wget -v {filename} -O {output_file}")
    logger.info(f"StdOut message: {std_out}")
    logger.info(f"StdErr message: {std_err}")

    mapping = pandas.read_excel(output_file)
    mapping["field name"] = mapping["table"].str.lower() + "." + mapping["field name"]
    mapping["code/format"] = mapping["code/format"].astype(str)

    return mapping


@asset(
    partitions_def=StaticPartitionsDefinition(years),
    group_name="3_apply_preprocessing",
    io_manager_key="s3_io_manager",
    compute_kind="pandas",
)
def accidents_vehicles_casualties_unify(
    accidents_vehicles_casualties_merged: pandas.DataFrame,
    categorical_mapping: pandas.DataFrame,
) -> pandas.DataFrame:
    """
    Replace ids by labels: Combination of accidents, vehicles and casualties.
    Clean and unify missing values to a None values. Apply date(-time)
    conversion of date and time columns.
    """

    logger = get_dagster_logger()

    decode_mapping = {}

    mapping_groupby = categorical_mapping.dropna(subset="label", how="any").groupby(
        "field name"
    )[["code/format", "label"]]

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

    X = accidents_vehicles_casualties_merged
    for column in X.columns:
        if column in decode_mapping:
            logger.info(f"Decoding column: {column}")
            X[column] = X[column].replace(decode_mapping[column])

    # Based on following pattern, set all matches to None
    pattern = r"(?i)data\s*missing|unknown|undefined"

    # Unify column handling and correct errors
    oor = "Data missing or out of range"
    logger.info("Unifying incorrect columns")
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
        X[column] = X[column].replace(to_replace=pattern, value=None, regex=True)

    # Convert date and time columns to specific pandas objects
    X["accident.time"] = pandas.to_timedelta(X["accident.time"] + ":00")
    X["accident.date"] = pandas.to_datetime(X["accident.date"], format="%d/%m/%Y")

    return X


@asset(
    partitions_def=StaticPartitionsDefinition(years),
    group_name="3_apply_preprocessing",
    io_manager_key="s3_io_manager",
    compute_kind="pandas",
)
def accidents_vehicles_casualties_preprocessed(
    accidents_vehicles_casualties_unify: pandas.DataFrame,
) -> pandas.DataFrame:
    """
    Apply preprocessing on dataset to enable machine learning model application.
    """

    categorization = load_yaml(Path(settings.CONFIG_DIR) / "categorization.yaml")

    X = accidents_vehicles_casualties_unify
    X = X.set_index("accident.accident_index")

    # Define target, i.e. casualty severity level
    X["target"] = X.pop("casualty.casualty_severity").replace(
        {np.nan: 0, "Slight": 1, "Serious": 2, "Fatal": 3}
    )
    X = X.loc[:, ~X.columns.str.startswith("casualty.")]
    X = X.drop_duplicates()

    n_vehicles = X.groupby(level=0)["vehicle.vehicle_reference"].nunique()
    X["accident.n_vehicles"] = np.nan
    X["accident.n_vehicles"].loc[n_vehicles.index] = n_vehicles.loc[n_vehicles.index]

    # Columns in training dataset
    columns = (
        categorization["spatiotemporal_properties"]
        + categorization["vehicle_properties"]
        + categorization["environmental_properties"]
        + ["accident.n_vehicles", "target"]
    )
    X = X[columns]

    # Make vehicle columns categorical, so we can multiple vehicle properties
    # one row
    for column in ["vehicle.engine_capacity_cc", "vehicle.age_of_vehicle"]:

        agg = (
            lambda x: f"{column}#{x}"  # pylint: disable=unnecessary-lambda-assignment,cell-var-from-loop
        )
        X[column] = pandas.qcut(
            X[column],
            settings.CATEGORIZATION_BIN_ENDGES,
            labels=list(map(agg, range(settings.CATEGORIZATION_BIN_ENDGES))),
            duplicates="drop"
        ).astype(object)

    # Transform data(-time) columns
    X["accident.month"] = X["accident.date"].dt.month
    X["accident.weekday"] = X["accident.date"].dt.dayofweek
    X["accident.hour"] = X["accident.time"].dt.total_seconds() / 60 / 60

    X["date"] = X.pop("accident.date")
    X.pop("accident.time")

    X = fillna_categorical(X)

    # Group-agg by accident_index:
    # Vehicle columns are simply summerized, such that strings (possibly iden-
    # tifying categories) are concatenated
    # Other columns are unique anyway
    # Target column is summarized to mimic a total accident severity score
    vehicle_columns = X.columns[X.columns.str.startswith("vehicle.")]
    other_columns = [
        column for column in X if column not in vehicle_columns and column != "target"
    ]
    for column in vehicle_columns:
        X[column] = X[column].astype(str)

    agg = {
        **{column: " ".join for column in vehicle_columns},
        **{column: "first" for column in other_columns},
        **{"target": "sum"},
    }

    X = fillna_categorical(X)

    return X.groupby(level=0).agg(agg)


@asset(
    group_name="3_apply_preprocessing",
    io_manager_key="s3_io_manager",
    compute_kind="pandas",
)
def accidents_vehicles_casualties_dataset(
    accidents_vehicles_casualties_preprocessed: Dict[str, pandas.DataFrame]
) -> pandas.DataFrame:
    """
    Merge partitions into single data asset.
    """

    X = pandas.concat(accidents_vehicles_casualties_preprocessed.values(), axis=0)

    # Establish dtype safety: There are some issues using type conversion
    # when finally using the data for inference making via api
    for column in X:
        if X[column].dtype == np.int32:
            X[column] = X[column].astype(int)
        elif X[column].dtype == np.float32:
            X[column] = X[column].astype(float)

    return X
