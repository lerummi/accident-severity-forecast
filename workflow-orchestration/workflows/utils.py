import pandas
import yaml
from pathlib import Path
from pandas.api.types import (
    is_numeric_dtype,
    is_datetime64_any_dtype,
    is_timedelta64_dtype
)
from typing import Union
import subprocess


def runcmd(cmd, *args, **kwargs):
    """
    Run unix command in python function. 
    """

    process = subprocess.Popen(
        cmd,
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE,
        text = True,
        shell = True
    )
    std_out, std_err = process.communicate()
    
    return std_out.strip(), std_err


def is_numeric_or_datelike(series: pandas.Series) -> bool:

    return (
        is_numeric_dtype(series) |
        is_datetime64_any_dtype(series) |
        is_timedelta64_dtype(series)
    )


def load_yaml(yamlfile: Union[Path, str]):

    if isinstance(yamlfile, str):
        yamlfile = Path(str)

    return yaml.safe_load(yamlfile.read_text())
