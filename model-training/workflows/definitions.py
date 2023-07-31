from dagster import Definitions
from dagster import load_assets_from_modules
from dagstermill import ConfigurableLocalOutputNotebookIOManager

from . import assets


defs = Definitions(
    assets=load_assets_from_modules(
        modules=[
            assets
        ],
    ),
    resources={
        "output_notebook_io_manager": 
            ConfigurableLocalOutputNotebookIOManager()
    }
)