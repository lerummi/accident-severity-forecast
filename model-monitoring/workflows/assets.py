import pandas

from dagster import asset
from dagster import SourceAsset, AssetKey

accidents_vehicles_casualties_dataset = SourceAsset(
    key=AssetKey("accidents_vehicles_casualties_dataset"),
    io_manager_key="s3_io_manager"
)


@asset(
    io_manager_key="s3_io_manager",
    compute_kind="pandas"
)
def test_accidents_vehicles_casualties_dataset(
    context,
    accidents_vehicles_casualties_dataset
) -> pandas.DataFrame:
    """
    Test loading from S3
    """
    

    return pandas.DataFrame()
