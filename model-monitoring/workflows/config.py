from pydantic import BaseSettings, Field


class Settings(BaseSettings):

    PREDICT_URL: str = Field("http://0.0.0.0:8000/predict", env="PREDICT_URL")
    SIMULATION_START_DATE: str = Field("2017-01-01", env="SIMULATION_START_DATE")
    INITIAL_UNIX_TIMESTAMP: str = Field("0", env="INITIAL_UNIX_TIMESTAMP")
    SECONDS_PER_DAY: str = Field("10", env="SECONDS_PER_DAY")
    WORKFLOW_DATA_BUCKET: str = Field("/tmp/workflow_data_bucket", env="WORKFLOW_DATA_BUCKET")
    S3_ENDPOINT_URL: str = Field("http://minio:9000", env="S3_ENDPOINT_URL")


settings = Settings()