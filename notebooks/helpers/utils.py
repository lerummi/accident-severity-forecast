import os
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
    Read all partitions associcated with a specific asset and concatenate
    to pandas.DataFrame
    """

    assets_dir = Path(os.environ["DATA_DIR"]) / "assets"

    directory = assets_dir / asset
    if not directory.exists():
        raise IOError(
            f"Apparently and asset '{asset}' is not available in the storage "
            f"directory {assets_dir}"
        )

    return pandas.concat(
        pandas.read_parquet(file) for file in directory.glob("**/*.parquet")
    )
