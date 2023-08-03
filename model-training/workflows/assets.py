import pandas
from dagstermill import define_dagstermill_asset
from dagster import file_relative_path
from dagster import asset
from dagster import SourceAsset, AssetKey, AssetIn


accidents_vehicles_casualties_dataset = SourceAsset(
    key=AssetKey("accidents_vehicles_casualties_dataset"),
    io_manager_key="s3_io_manager"
)


@asset(
    io_manager_key="s3_io_manager",
    compute_kind="pandas"
)
def loaded_accidents_vehicles_casualties_dataset(
    context,
    accidents_vehicles_casualties_dataset
) -> pandas.DataFrame:
    """
    Load complete dataset to make it available for training.
    """

    return accidents_vehicles_casualties_dataset


jupyter_notebook_asset = define_dagstermill_asset(
    name="accident_severity_model_training",
    notebook_path=file_relative_path(
        __file__, 
        "../../notebooks/predictive-modeling.ipynb"
    ),
    io_manager_key="output_notebook_io_manager",
    ins={"X": AssetIn("loaded_accidents_vehicles_casualties_dataset")}
)
