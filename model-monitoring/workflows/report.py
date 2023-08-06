from logging import Logger
from typing import Any, Dict, List

import pandas

# For some reason loading evidently takes ages. By shifting the
# import into this module, it is only loaded from the specific asset
# materialization is happening.
from evidently import ColumnMapping
from evidently.metrics import (
    ColumnDriftMetric,
    DatasetDriftMetric,
    DatasetMissingValuesMetric,
)
from evidently.report import Report


def make_evidently_report(
    reference_data: pandas.DataFrame,
    evaluation_data: pandas.DataFrame,
    column_dtypes: Dict[str, List],
    logger: Logger,
) -> List[Dict[str, Any]]:
    """
    Given reference data and evaluation data, generate evidently report.
    Currently, prediction column drift, dataset drift and missing values is
    monitored.
    """

    # Initialize report properties
    report = Report(
        metrics=[
            ColumnDriftMetric(column_name="predictions"),
            DatasetDriftMetric(),
            DatasetMissingValuesMetric(),
        ]
    )

    # Derive column mapping
    column_mapping = ColumnMapping(
        target=None,
        prediction="predictions",
        numerical_features=column_dtypes["numerical"],
        categorical_features=column_dtypes["categorical"],
    )

    start_date = evaluation_data["date"].min()
    end_date = evaluation_data["date"].max()

    logger.info(f"Creating reports for date interval: [{start_date, end_date}]")

    # Loop over individual dates and create report
    results = []
    for date in pandas.date_range(start=start_date, end=end_date):
        eval_single = evaluation_data[evaluation_data["date"] == date]

        logger.info(f"Creating report for {date} with {len(eval_single)} events.")

        if eval_single.empty:
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

    return results
