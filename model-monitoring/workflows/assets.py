import os
import pandas
import requests
from dagster import asset
from dagster import get_dagster_logger
from dagster import AutoMaterializePolicy
from dagster import FreshnessPolicy
from dagster import SourceAsset, AssetKey
from evidently import ColumnMapping
from evidently.report import Report
from evidently.metrics import (
    ColumnDriftMetric,
    DatasetDriftMetric,
    DatasetMissingValuesMetric
)

from .utils import (
    get_simulation_date, 
    read_pandas_asset,
    infer_feature_types
)


inc = int(os.environ["EVAL_SCHEDULER_INCREMENT"])


accidents_vehicles_casualties_dataset = SourceAsset(
    key=AssetKey("accidents_vehicles_casualties_dataset"),
    io_manager_key="s3_io_manager"
)


@asset(
    io_manager_key="db_io_manager",
    compute_kind="postgres"
)
def accidents_reference_dataset(
    context,
    accidents_vehicles_casualties_dataset
) -> pandas.DataFrame:
    """
    Filter accidents associated with the training data.
    """

    logger = get_dagster_logger()
    X = accidents_vehicles_casualties_dataset
    X = X[X["date"] < pandas.to_datetime(os.environ["SIMULATION_START_DATE"])]

    X.pop("date")
    X.pop("target")

    return X


@asset(
    io_manager_key="s3_io_manager",
    compute_kind="pandas",
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=int(inc)),
    auto_materialize_policy=AutoMaterializePolicy.eager()
)
def processed_interval_reminder(
    context,
) -> pandas.Series:
    """Reminded date interval already processed"""

    current_date = get_simulation_date()
    logger = get_dagster_logger()

    try:
        processed = read_pandas_asset("processed_interval_reminder")
        logger.info("Found existing processed_interval_reminder.")
        if current_date < processed["last_processed_date"]:
            logger.info("Last date processed is greater than current_date.")
            raise ValueError
        
        processed["last_processed_date"] = processed["current_date"]
        processed["current_date"] = current_date
    except:
        logger.info("Defaulting to initialization of processing dates.")
        processed = pandas.Series(
            [
                pandas.to_datetime(os.environ["SIMULATION_START_DATE"]),
                current_date
            ], index=["last_processed_date", "current_date"]
        )

    logger.info(processed.to_dict())

    return processed


@asset(
    io_manager_key="db_io_manager",
    compute_kind="postgres",
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=int(inc)),
    auto_materialize_policy=AutoMaterializePolicy.eager()
)
def recent_accidents_dataset(
    context,
    processed_interval_reminder,
    accidents_vehicles_casualties_dataset
) -> pandas.DataFrame:
    """
    Filter accidents according to date interval to simulate time evolution.
    """

    processed = read_pandas_asset("processed_interval_reminder")
    start_date = processed["last_processed_date"]
    end_date = processed["current_date"]

    logger = get_dagster_logger()
    X = accidents_vehicles_casualties_dataset
    X = X[
        (X["date"] >= start_date) & 
        (X["date"] < end_date)
    ]
    logger.info(f"Processing {len(X)} new accidents.")

    return X


@asset(
    io_manager_key="db_io_manager",
    compute_kind="postgres",
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=int(inc)),
    auto_materialize_policy=AutoMaterializePolicy.eager()
)
def accidents_predictions(
    context,
    recent_accidents_dataset
) -> pandas.DataFrame:
    """
    For new accident data request prediction from model.
    """

    X = recent_accidents_dataset
    X = X.fillna("nan")

    index = X.pop("accident.accident_index")
    date = X.pop("date")
    X.pop("target")

    logger = get_dagster_logger()
    logger.info(
        "Requestion predictions from http://deployed-model:8000/predict"
    )

    headers = {"Content-type": "application/json"}

    response = requests.post(
        "http://deployed-model:8000/predict",
        json=X.to_dict("records"),
        headers=headers
    )

    if response.status_code != 200:
        raise Exception(
            "Endpoint 'http://deployed-model:8000/predict' returned "
            f"status code {response.status_code}. Error text: {response.text}."
        )

    predictions = response.json()
    result = pandas.DataFrame.from_dict(predictions)
    result["date"] = date
    result.index = index
    return result


@asset(
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=int(inc)),
    auto_materialize_policy=AutoMaterializePolicy.eager()
)
def evidently_report(
    context,
    accidents_reference_dataset,
    recent_accidents_dataset,
    accidents_predictions
):
    """
    For recent dataset compute evidently report.
    """

    accidents_reference_dataset.pop("date")
    accidents_predictions.pop("date")

    columns = accidents_reference_dataset.columns

    dtypes = infer_feature_types(columns)
    dtypes["numerical"] = [
        column for column in columns
        if not column in dtypes["categorical"] + dtypes["text"]
    ]

    report = Report(
        metrics=[
            ColumnDriftMetric(column_name="predictions"),
            DatasetDriftMetric(),
            DatasetMissingValuesMetric()
        ]
    )

    column_mapping = ColumnMapping(
        target=None,
        prediction="predictions",
        numerical_features=dtypes["numerical"],
        categorical_features=dtypes["categorical"],
        text_features=dtypes["text"]
    )

    # Create evaluation dataset by merging recent_accidents to predictions
    eval_data = recent_accidents_dataset.merge(
        accidents_predictions,
        on="accident.accident_index",
        how="left"
    )
    report.run(
        reference_data=accidents_reference_dataset,
        current_data=recent_accidents_dataset,
        column_mapping=column_mapping
    )

    metrics = report.as_dict()["metrics"]

    prediction_drift = metrics[0]["result"]["drift_score"]
    num_drifted_columns = metrics[1]["result"]["number_of_drifted_columns"]
    share_missing_values = metrics[2]["result"]["current"][
        "share_of_missing_values"
    ]