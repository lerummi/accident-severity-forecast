from pydantic import BaseSettings, Field


class Settings(BaseSettings):  # pylint: disable=too-few-public-methods
    """
    Settings for service.
    """

    WORKFLOW_DATA_BUCKET: str = Field(
        "/tmp/workflow_data_bucket", env="WORKFLOW_DATA_BUCKET"
    )
    LOCAL_FOLDER: str = Field("/tmp", env="LOCAL_FOLDER")


settings = Settings()
