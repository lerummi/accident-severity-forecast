import datetime
import time
from pathlib import Path
from typing import List

import boto3
import pandas
from botocore.exceptions import ClientError
from workflows.config import settings


def get_simulation_date(current_timestamp=None):
    """
    Establish time warp by updating simulated date starting from
    SIMULATION_START_DATE based on the number of days passing per (real
    second, i.e. SECONDS_PER_DAY.
    """

    simulation_date = pandas.to_datetime(settings.SIMULATION_START_DATE)
    initial_timestamp = float(settings.INITIAL_UNIX_TIMESTAMP)
    if current_timestamp is None:
        current_timestamp = float(time.time())
    seconds_per_day = float(settings.SECONDS_PER_DAY)

    days_gone = (current_timestamp - initial_timestamp) / seconds_per_day
    days_gone = datetime.timedelta(days=days_gone)

    return pandas.to_datetime((simulation_date + days_gone).date())


def read_pandas_asset(asset: str) -> pandas.DataFrame:
    """
    Download pickle DataFrame from S3 bucket and return it
    """

    BUCKET_NAME = settings.WORKFLOW_DATA_BUCKET
    LOCAL_FOLDER = Path(settings.LOCAL_DIR)

    s3_client = boto3.client("s3", endpoint_url=settings.S3_ENDPOINT_URL)

    try:
        s3_client.download_file(BUCKET_NAME, asset, LOCAL_FOLDER / asset)
        with open(LOCAL_FOLDER / asset, "rb") as input_file:
            data = pandas.read_pickle(input_file)
    except ClientError as e:
        print(asset, "- failed to download from S3, so terminate.")
        print(e)
        raise e
    if not isinstance(data, (pandas.DataFrame, pandas.Series)):
        exception_message = (
            f"{asset} - is not a pandas DataFrame, strange, raise Exception"
        )
        print(exception_message)
        raise ImportError(exception_message)
    # here you can check the columns of the DataFrame
    print(asset, "- downloaded OK, passed checks")

    return data


def infer_feature_types(
    X: pandas.DataFrame, skip: List = None, max_categorical_nunique: int = 10
):
    """
    Automatically infer the datatypes numerical, categorical, and text from
    input DataFrame.
    """

    categorical = []
    text = []
    numerical = []

    if skip is None:
        skip = []

    for column in X:
        if column in skip:
            continue
        if X[column].dtype == object:
            if X[column].nunique() > max_categorical_nunique:
                text.append(column)
            else:
                categorical.append(column)
        else:
            numerical.append(column)

    return {"categorical": categorical, "text": text, "numerical": numerical}
