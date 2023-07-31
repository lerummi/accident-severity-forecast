from dagster import Definitions
from dagster import load_assets_from_modules

from workflows.assets import accidents

from workflows.io import PandasIOManager, PartionedPandasIOManager


defs = Definitions(
    assets=load_assets_from_modules(
        modules=[
            accidents
        ],
    ),
    resources={
        "partitioned_io_manager": PartionedPandasIOManager(),
        "pandas_io_manager": PandasIOManager()
    }
)