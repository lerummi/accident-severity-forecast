from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):  # pylint: disable=too-few-public-methods
    """
    Settings for service.
    """

    MODEL_NAME: str = Field("accident-severity", env="MODEL_NAME")
    MODEL_VERSION: str = Field("1", env="MODEL_VERSION")


settings = Settings()
