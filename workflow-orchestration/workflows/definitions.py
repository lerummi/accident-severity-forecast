from dagster import Definitions
from workflows.jobs import process_accidents

from workflows.io import PandasIOManager


defs = Definitions(
    jobs=[process_accidents],
    resources={"io_manager": PandasIOManager()}
)
