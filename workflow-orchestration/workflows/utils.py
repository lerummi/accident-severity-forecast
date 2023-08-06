import subprocess
from logging import Logger
from pathlib import Path
from typing import Union

import pandas
import yaml
from pandas.api.types import (
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_timedelta64_dtype,
)
from workflows.config import settings


def runcmd(cmd):
    """
    Run unix command in python function.
    """

    process = subprocess.Popen(  # pylint: disable=consider-using-with
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True
    )
    std_out, std_err = process.communicate()

    return std_out.strip(), std_err


def is_numeric_or_datelike(series: pandas.Series) -> bool:
    """
    Infer probable datelike behavior for time series.
    """
    return (
        is_numeric_dtype(series)
        | is_datetime64_any_dtype(series)
        | is_timedelta64_dtype(series)
    )


def load_yaml(yamlfile: Union[Path, str]):
    """
    Load yaml file.
    """
    if isinstance(yamlfile, str):
        yamlfile = Path(str)

    return yaml.safe_load(yamlfile.read_text())  # pylint: disable=unspecified-encoding


def fillna_categorical(X: pandas.DataFrame):
    """
    For all categorical columns replace nan by 'None'.
    """
    for column in X:
        if X[column].dtype == object:
            X[column] = X[column].fillna("None")
    return X


def download_raw_files(scope: str, year: str, logger: Logger):
    """
    Download raw csv files from UK Road Safety base url.
    """

    output_dir = Path(settings.DATA_DIR) / "raw"
    base_url = settings.BASE_URL
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = "/".join([base_url, f"dft-road-casualty-statistics-{scope}-{year}.csv"])

    output_file = output_dir / f"{scope}-{year}.csv"

    logger.info(f"Running wget -v {filename} -O {output_file}")
    std_out, std_err = runcmd(f"wget -v {filename} -O {output_file}")
    logger.info(f"StdOut message: {std_out}")
    logger.info(f"StdErr message: {std_err}")

    return pandas.read_csv(output_file, low_memory=False)
