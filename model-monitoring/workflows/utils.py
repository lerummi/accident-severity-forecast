import datetime
import os
import time
from typing import List

import boto3
import pandas


def get_simulation_date():
    """
    Establish time warp by updating simulated date starting from
    SIMULATION_START_DATE based on the number of days passing per (real) second, i.e. SECONDS_PER_DAY.
    """

    simulation_date = pandas.to_datetime(os.environ["SIMULATION_START_DATE"])
    initial_timestamp = float(os.environ["INITIAL_UNIX_TIMESTAMP"])
    current_timestamp = float(time.time())
    seconds_per_day = float(os.environ["SECONDS_PER_DAY"])

    days_gone = (current_timestamp - initial_timestamp) / seconds_per_day
    days_gone = datetime.timedelta(days=days_gone)

    return pandas.to_datetime((simulation_date + days_gone).date())


def read_pandas_asset(asset: str) -> pandas.DataFrame:
    """
    Download pickle DataFrame from S3 bucket and return it
    """

    BUCKET_NAME = os.environ["WORKFLOW_DATA_BUCKET"]
    LOCAL_FOLDER = "/tmp/"

    s3_client = boto3.client("s3", endpoint_url=os.environ.get("S3_ENDPOINT_URL", None))

    try:
        s3_client.download_file(BUCKET_NAME, asset, LOCAL_FOLDER + asset)
        with open(LOCAL_FOLDER + asset, "rb") as input_file:
            data = pandas.read_pickle(input_file)
    except Exception as e:
        print(asset, "- failed to download from S3, so terminate.")
        print(e)
        raise e
    if not isinstance(data, (pandas.DataFrame, pandas.Series)):
        exception_message = (
            asset + "- is not a pandas DataFrame, strange, raise Exception"
        )
        print(exception_message)
        raise Exception(exception_message)
    # here you can check the columns of the DataFrame
    print(asset, "- downloaded OK, passed checks")

    return data


def infer_feature_types(
    X: pandas.DataFrame, skip: List = None, max_categorical_nunique: int = 10
):

    categorical = []
    text = []
    numerical = []

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
