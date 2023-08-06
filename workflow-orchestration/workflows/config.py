from pathlib import Path
from typing import List

import numpy as np
from pydantic import BaseSettings, Field


class Settings(BaseSettings):

    DATA_DIR: str = Field("/tmp/accidents_data", env="DATA_DIR")
    CONFIG_DIR: str = Field("/tmp/accidents_data/config", env="CONFIG_DIR")
    BASE_URL: str = "https://data.dft.gov.uk/road-accidents-safety-data"
    YEARS_TO_PROCESS: List = list(np.arange(2016, 2018).astype(str))

    CATEGORIZATION_BIN_ENDGES: int = 10


settings = Settings()
