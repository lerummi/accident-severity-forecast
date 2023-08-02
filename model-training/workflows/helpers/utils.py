import os
import boto3
import pandas
from pandas.api.types import (
    is_numeric_dtype,
    is_datetime64_any_dtype,
    is_timedelta64_dtype
)
from pandas.core.dtypes.dtypes import CategoricalDtype
from typing import Union
from pathlib import Path
import yaml


def load_yaml(yamlfile: Union[Path, str]):

    if isinstance(yamlfile, str):
        yamlfile = Path(str)

    return yaml.safe_load(yamlfile.read_text())


def infer_catboost_feature_types(X: pandas.DataFrame, max_categorical_nunique: int = 10):
    
    categorical = []
    text = []
    
    for column in X:
        if X[column].dtype in (object, CategoricalDtype):
            if X[column].nunique() > max_categorical_nunique:
                text.append(column)
            else:
                categorical.append(column)
                
    return {
        "categorical": categorical, 
        "text": text
    }


def read_partitioned_pandas_asset(asset: str) -> pandas.DataFrame:
    """
    Download pickle DataFrame from S3 bucket and return it
    """

    BUCKET_NAME = os.environ["WORKFLOW_DATA_BUCKET"]
    LOCAL_FOLDER = "/tmp/"

    s3_client = boto3.client(
        "s3", 
        endpoint_url=os.environ.get("S3_ENDPOINT_URL", None)
    )

    try:
        s3_client.download_file(BUCKET_NAME, asset, LOCAL_FOLDER + asset)
        with open(LOCAL_FOLDER + asset, "rb") as input_file:
            data = pandas.read_pickle(input_file)
    except Exception as e:
        print(asset, "- failed to download from S3, so terminate.")
        print(e)
        raise e
    if not isinstance(data, pandas.DataFrame):
        exception_message = (
            asset + "- is not a pandas DataFrame, strange, raise Exception"
        )
        print(exception_message)
        raise Exception(exception_message)
    # here you can check the columns of the DataFrame
    print(asset, "- downloaded OK, passed checks")

    return data
