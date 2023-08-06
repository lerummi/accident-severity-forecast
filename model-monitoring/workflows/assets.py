import pandas
from botocore.exceptions import ClientError
from dagster import (
    AssetKey,
    AutoMaterializePolicy,
    FreshnessPolicy,
    SourceAsset,
    asset,
    get_dagster_logger,
)

from workflows.inference import make_prediction
from workflows.utils import get_simulation_date, infer_feature_types, read_pandas_asset
from workflows.config import settings


inc = int(settings.EVAL_SCHEDULER_INCREMENT)


accidents_vehicles_casualties_dataset = SourceAsset(
    key=AssetKey("accidents_vehicles_casualties_dataset"),
    io_manager_key="s3_io_manager",
    group_name="reference",
)


@asset(group_name="reference", io_manager_key="db_io_manager", compute_kind="postgres")
def reference_accidents_dataset(
    accidents_vehicles_casualties_dataset,
) -> pandas.DataFrame:
    """
    Filter accidents associated with the training data. Only use a downsampled
    datapoints to make evaluation with evidently applicable.
    """

    X = accidents_vehicles_casualties_dataset
    X = X[X["date"] < pandas.to_datetime(settings.SIMULATION_START_DATE)]
    X = X.sample(n=settings.REFERENCE_DATA_SIZE)

    X.pop("target")

    return X


@asset(group_name="reference", io_manager_key="db_io_manager", compute_kind="postgres")
def reference_accidents_predictions(reference_accidents_dataset) -> pandas.DataFrame:
    """
    For reference accident data request prediction from model.
    """

    logger = get_dagster_logger()
    logger.info(f"Requestion predictions from {settings.PREDICT_URL}")

    return make_prediction(reference_accidents_dataset)


@asset(
    group_name="recent",
    io_manager_key="s3_io_manager",
    compute_kind="pandas",
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=int(inc)),
    auto_materialize_policy=AutoMaterializePolicy.eager(),
)
def recent_interval_processor() -> pandas.Series:
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
    except (ClientError, ValueError):
        logger.info("Defaulting to initialization of processing dates.")
        processed = pandas.Series(
            [pandas.to_datetime(settings.SIMULATION_START_DATE), current_date],
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
    recent_interval_processor,  # pylint: disable=unused-argument
    accidents_vehicles_casualties_dataset,
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
def recent_accidents_predictions(recent_accidents_dataset) -> pandas.DataFrame:
    """
    For new accident data request prediction from model.
    """

    logger = get_dagster_logger()

    # Only process, if recent accidents are available
    if recent_accidents_dataset.empty:
        logger.info("No accidents found! Skipping.")
        return pandas.DataFrame()

    logger.info(f"Requestion predictions from {settings.PREDICT_URL}")
    return make_prediction(recent_accidents_dataset)


@asset(
    group_name="recent",
    io_manager_key="recent_io_manager",
    compute_kind="postgres",
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=int(inc)),
    auto_materialize_policy=AutoMaterializePolicy.eager(),
)
def recent_evidently_report(
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
    if recent_accidents_dataset.empty:
        logger.info("No accidents found! Skipping.")
        return pandas.DataFrame()

    # For some reason loading evidently takes ages. By shifting the
    # import into this module, it is only loaded from the specific asset
    # materialization is happening.
    logger.info("Busy loading report tools")
    from .report import make_evidently_report  # pylint: disable=import-outside-toplevel

    logger.info("Finished importing")

    dtypes = infer_feature_types(
        reference_accidents_dataset, skip=["date", "accident.accident_index"]
    )

    # Remove all text columns, because this seems to make problems in
    # evidently
    for column in dtypes["text"]:
        recent_accidents_dataset.pop(column)
        reference_accidents_dataset.pop(column)
    dtypes.pop("text")

    # Create evaluation dataset by merging recent_accidents to predictions
    reference_data = reference_accidents_dataset.merge(
        reference_accidents_predictions,
        on="accident.accident_index",
        how="left",
        suffixes=("", "_p"),
    )
    evaluation_data = recent_accidents_dataset.merge(
        recent_accidents_predictions,
        on="accident.accident_index",
        how="left",
        suffixes=("", "_p"),
    )

    results = make_evidently_report(
        reference_data, evaluation_data, column_dtypes=dtypes, logger=logger
    )

    return pandas.DataFrame(results)
