"""Collection of Cereal jobs"""
from dagster import job

from workflows.assets import accidents
from workflows.io import PandasIOManager


@job(resource_defs={"io_manager": PandasIOManager()})
def process_accidents():
    """
    Process all accidents, vehicle and casualty data.
    """

    accident_df = accidents.raw_accidents()
    vehicle_df = accidents.raw_vehicles()
    casualty_df = accidents.raw_casualties()
    mapping_df = accidents.categorical_mapping()

    X = accidents.accidents_vehicles_merged(accident_df, vehicle_df)
    X = accidents.accidents_vehicles_casualties_merged(X, casualty_df)

    X = accidents.accidents_vehicles_casualties_unify(X, mapping_df)

