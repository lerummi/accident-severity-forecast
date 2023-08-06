from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):

    MODEL_NAME: str = Field("accident-severity", env="MODEL_NAME")
    MODEL_VERSION: str = Field("1", env="MODEL_VERSION")


settings = Settings()
