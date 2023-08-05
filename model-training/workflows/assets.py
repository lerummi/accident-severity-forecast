import pandas
from dagster import AssetIn, AssetKey, SourceAsset, asset, file_relative_path
from dagstermill import define_dagstermill_asset

# This asset is only needed, because define_dagstermill_asset can not
# directly get input from SourceAsset via the 'ins' argument, here strictly
# a AssetIn is required, which, however can not be used to load from foreign
# code base
accidents_vehicles_casualties_dataset = SourceAsset(
    key=AssetKey("accidents_vehicles_casualties_dataset"),
    io_manager_key="s3_io_manager",
)


@asset(io_manager_key="s3_io_manager", compute_kind="pandas")
def loaded_accidents_vehicles_casualties_dataset(
    context, accidents_vehicles_casualties_dataset
) -> pandas.DataFrame:
    """
    Load complete dataset to make it available for training.
    """

    return accidents_vehicles_casualties_dataset


jupyter_notebook_asset = define_dagstermill_asset(
    name="accident_severity_model_training",
    notebook_path=file_relative_path(
        __file__, "../../notebooks/predictive-modeling.ipynb"
    ),
    io_manager_key="output_notebook_io_manager",
    ins={"X": AssetIn("loaded_accidents_vehicles_casualties_dataset")},
    description="Run training notebook, log metrics and (registered) "
    "model to MLflow",
)
