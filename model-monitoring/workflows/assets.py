import os

import pandas
import requests
from dagster import (
    AssetKey,
    AutoMaterializePolicy,
    FreshnessPolicy,
    SourceAsset,
    asset,
    get_dagster_logger,
)

from .inference import make_prediction
from .utils import get_simulation_date, infer_feature_types, read_pandas_asset

inc = int(os.environ["EVAL_SCHEDULER_INCREMENT"])


accidents_vehicles_casualties_dataset = SourceAsset(
    key=AssetKey("accidents_vehicles_casualties_dataset"),
    io_manager_key="s3_io_manager",
    group_name="reference",
)


@asset(group_name="reference", io_manager_key="db_io_manager", compute_kind="postgres")
def reference_accidents_dataset(
    context, accidents_vehicles_casualties_dataset
) -> pandas.DataFrame:
    """
    Filter accidents associated with the training data. Only use 10000
    datapoints to make evaluation with evidently applicable.
    """

    logger = get_dagster_logger()
    X = accidents_vehicles_casualties_dataset
    X = X[X["date"] < pandas.to_datetime(os.environ["SIMULATION_START_DATE"])]
    X = X.sample(n=10000)

    X.pop("target")

    return X


@asset(group_name="reference", io_manager_key="db_io_manager", compute_kind="postgres")
def reference_accidents_predictions(
    context, reference_accidents_dataset
) -> pandas.DataFrame:
    """
    For reference accident data request prediction from model.
    """

    logger = get_dagster_logger()
    logger.info(f"Requestion predictions from {os.environ['PREDICT_URL']}")

    return make_prediction(reference_accidents_dataset)


@asset(
    group_name="recent",
    io_manager_key="s3_io_manager",
    compute_kind="pandas",
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=int(inc)),
    auto_materialize_policy=AutoMaterializePolicy.eager(),
)
def recent_interval_processor(
    context,
) -> pandas.Series:
    """Reminded date interval already processed"""

    current_date = get_simulation_date()
    logger = get_dagster_logger()

    try:
        processed = read_pandas_asset("recent_interval_processor")
        logger.info("Found existing recent_interval_processor.")
        if current_date < processed["current_date"]:
            logger.info("Last date processed is greater than current_date.")
            raise ValueError

        processed["last_processed_date"] = processed["current_date"]
        processed["current_date"] = current_date
    except:
        logger.info("Defaulting to initialization of processing dates.")
        processed = pandas.Series(
            [pandas.to_datetime(os.environ["SIMULATION_START_DATE"]), current_date],
            index=["last_processed_date", "current_date"],
        )

    logger.info(processed.to_dict())

    return processed


@asset(
    group_name="recent",
    io_manager_key="recent_io_manager",
    compute_kind="postgres",
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=int(inc)),
    auto_materialize_policy=AutoMaterializePolicy.eager(),
)
def recent_accidents_dataset(
    context, recent_interval_processor, accidents_vehicles_casualties_dataset
) -> pandas.DataFrame:
    """
    Filter accidents according to date interval to simulate time evolution.
    """

    processed = read_pandas_asset("recent_interval_processor")
    start_date = processed["last_processed_date"]
    end_date = processed["current_date"]

    logger = get_dagster_logger()
    X = accidents_vehicles_casualties_dataset
    X = X[(X["date"] >= start_date) & (X["date"] < end_date)]
    X.pop("target")
    logger.info(f"Processing {len(X)} new accidents.")

    return X


@asset(
    group_name="recent",
    io_manager_key="recent_io_manager",
    compute_kind="postgres",
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=int(inc)),
    auto_materialize_policy=AutoMaterializePolicy.eager(),
)
def recent_accidents_predictions(context, recent_accidents_dataset) -> pandas.DataFrame:
    """
    For new accident data request prediction from model.
    """

    logger = get_dagster_logger()

    # Only process, if recent accidents are available
    if not len(recent_accidents_dataset):
        logger.info("No accidents found! Skipping.")
        return pandas.DataFrame()

    logger.info(f"Requestion predictions from {os.environ['PREDICT_URL']}")
    return make_prediction(recent_accidents_dataset)


@asset(
    group_name="recent",
    io_manager_key="recent_io_manager",
    compute_kind="postgres",
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=int(inc)),
    auto_materialize_policy=AutoMaterializePolicy.eager(),
)
def recent_evidently_report(
    context,
    reference_accidents_dataset,
    reference_accidents_predictions,
    recent_accidents_dataset,
    recent_accidents_predictions,
) -> pandas.DataFrame:
    """
    For recent dataset compute evidently report. For each day, compute report
    metrics and store it into database table.
    """

    logger = get_dagster_logger()

    # Only process, if recent accidents are available
    if not len(recent_accidents_dataset):
        logger.info("No accidents found! Skipping.")
        return pandas.DataFrame()

    # TODO: For some reason loading evidently takes ages. By shifting the
    # import into this module, it is only loaded from the specific asset
    # materialization is happening.
    logger.info("Busy importing evidently.")
    from evidently import ColumnMapping
    from evidently.metrics import (
        ColumnDriftMetric,
        DatasetDriftMetric,
        DatasetMissingValuesMetric,
    )
    from evidently.report import Report

    logger.info("Finished importing evidently.")

    dtypes = infer_feature_types(
        reference_accidents_dataset, skip=["date", "accident.accident_index"]
    )

    # TODO: Remove all text columns, because this seems to make problems in
    # evidently
    for column in dtypes["text"]:
        recent_accidents_dataset.pop(column)
        reference_accidents_dataset.pop(column)
    dtypes.pop("text")

    report = Report(
        metrics=[
            ColumnDriftMetric(column_name="predictions"),
            DatasetDriftMetric(),
            DatasetMissingValuesMetric(),
        ]
    )

    column_mapping = ColumnMapping(
        target=None,
        prediction="predictions",
        numerical_features=dtypes["numerical"],
        categorical_features=dtypes["categorical"],
    )

    # Create evaluation dataset by merging recent_accidents to predictions
    reference_data = reference_accidents_dataset.merge(
        reference_accidents_predictions,
        on="accident.accident_index",
        how="left",
        suffixes=("", "_p"),
    )
    eval_data = recent_accidents_dataset.merge(
        recent_accidents_predictions,
        on="accident.accident_index",
        how="left",
        suffixes=("", "_p"),
    )

    start_date = eval_data["date"].min()
    end_date = eval_data["date"].max()

    logger.info(f"Creating reports for date interval: [{start_date, end_date}]")

    results = []
    for date in pandas.date_range(start=start_date, end=end_date):
        eval_single = eval_data[eval_data["date"] == date]

        logger.info(f"Creating report for {date} with {len(eval_single)} events.")

        if not len(eval_single):
            continue

        report.run(
            reference_data=reference_data,
            current_data=eval_single,
            column_mapping=column_mapping,
        )

        metrics = report.as_dict()["metrics"]

        # Report to dictionary for later db insert
        results.append(
            {
                "date": date,
                "prediction_drift": metrics[0]["result"]["drift_score"],
                "num_drifted_columns": (
                    metrics[1]["result"]["number_of_drifted_columns"]
                ),
                "share_missing_values": (
                    metrics[2]["result"]["current"]["share_of_missing_values"]
                ),
            }
        )

    return pandas.DataFrame(results)
