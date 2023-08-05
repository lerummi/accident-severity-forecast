from dagster import Definitions, load_assets_from_modules
from dagster_aws.s3.io_manager import s3_pickle_io_manager
from dagster_aws.s3.resources import s3_resource
from workflows.assets import accidents

defs = Definitions(
    assets=load_assets_from_modules(
        modules=[accidents],
    ),
    resources={
        "s3_io_manager": s3_pickle_io_manager.configured(
            {"s3_bucket": {"env": "WORKFLOW_DATA_BUCKET"}, "s3_prefix": ""}
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
