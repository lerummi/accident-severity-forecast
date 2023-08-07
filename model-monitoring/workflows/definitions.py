from dagster import Definitions, define_asset_job, load_assets_from_modules
from dagster_aws.s3.io_manager import s3_pickle_io_manager
from dagster_aws.s3.resources import s3_resource

from . import assets, config, io

inc = config.settings.EVAL_SCHEDULER_INCREMENT


defs = Definitions(
    assets=load_assets_from_modules(modules=[assets]),
    jobs=[
        define_asset_job(
            "reference_data", selection=[assets.reference_accidents_dataset]
        )
    ],
    resources={
        "s3_io_manager": s3_pickle_io_manager.configured(
            {"s3_bucket": {"env": "WORKFLOW_DATA_BUCKET"}, "s3_prefix": ""}
        ),
        "db_io_manager": io.postgres_pandas_io_manager.configured(
            {
                "server": {"env": "POSTGRES_INFERENCE_SERVER"},
                "db": {"env": "POSTGRES_INFERENCE_DB"},
                "uid": {"env": "POSTGRES_INFERENCE_USER"},
                "pwd": {"env": "POSTGRES_INFERENCE_PASSWORD"},
                "port": {"env": "POSTGRES_INFERENCE_PORT"},
            }
        ),
        "recent_io_manager": io.recent_postgres_pandas_io_manager.configured(
            {
                "server": {"env": "POSTGRES_INFERENCE_SERVER"},
                "db": {"env": "POSTGRES_INFERENCE_DB"},
                "uid": {"env": "POSTGRES_INFERENCE_USER"},
                "pwd": {"env": "POSTGRES_INFERENCE_PASSWORD"},
                "port": {"env": "POSTGRES_INFERENCE_PORT"},
            }
        ),
        "s3": s3_resource.configured(
            {
                "region_name": {"env": "AWS_REGION"},
                "aws_access_key_id": {"env": "AWS_ACCESS_KEY_ID"},
                "aws_secret_access_key": {"env": "AWS_SECRET_ACCESS_KEY"},
                "endpoint_url": {"env": "S3_ENDPOINT_URL"},
            }
        ),
    },
)
