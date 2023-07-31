from dagstermill import define_dagstermill_asset
from dagster import file_relative_path


jupyter_notebook_asset = define_dagstermill_asset(
    name="accident_severity_model_training",
    notebook_path=file_relative_path(__file__, "../../notebooks/predictive-modeling.ipynb"),
    group_name="model_training",
    io_manager_key="output_notebook_io_manager"
)
