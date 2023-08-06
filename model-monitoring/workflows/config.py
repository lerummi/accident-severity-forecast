from pydantic import BaseSettings, Field


class Settings(BaseSettings):  # pylint: disable=too-few-public-methods
    """
    Settings for service.
    """

    PREDICT_URL: str = Field("http://0.0.0.0:8000/predict", env="PREDICT_URL")
    S3_ENDPOINT_URL: str = Field("http://minio:9000", env="S3_ENDPOINT_URL")
    WORKFLOW_DATA_BUCKET: str = Field(
        "/tmp/workflow_data_bucket", env="WORKFLOW_DATA_BUCKET"
    )
    LOCAL_DIR: str = "/tmp/"

    SIMULATION_START_DATE: str = Field("2017-01-01", env="SIMULATION_START_DATE")
    INITIAL_UNIX_TIMESTAMP: str = Field("0", env="INITIAL_UNIX_TIMESTAMP")
    SECONDS_PER_DAY: str = Field("10", env="SECONDS_PER_DAY")
    EVAL_SCHEDULER_INCREMENT: str = Field(2, env="EVAL_SCHEDULER_INCREMENT")

    REFERENCE_DATA_SIZE: int = 10000


settings = Settings()
