import pandas
from dagster import (
    InitResourceContext,
    InputContext,
    IOManager,
    OutputContext,
    StringSource,
    io_manager,
)
from sqlalchemy import create_engine

from .utils import read_pandas_asset


class PostgresDataframeIOManager(IOManager):
    """
    Persist fixed assets in postgres database.
    """

    def __init__(
        self, uid: str, pwd: str, server: str, db: str, port: str
    ):  # pylint: disable=too-many-arguments
        # credentials passed to IO Manager
        self.uid = uid
        self.pwd = pwd
        self.db = db
        self.server = server
        self.port = port

    def handle_output(self, context: OutputContext, obj: pandas.DataFrame):
        """
        Define output asset handling.
        """
        # Skip handling if the output is empty
        if obj.empty:
            return

        table_name = context.asset_key.to_python_identifier()

        engine = create_engine(
            f"postgresql://{self.uid}:{self.pwd}"
            f"@{self.server}:{self.port}/{self.db}"
        )

        obj.to_sql(table_name, engine, if_exists="replace", index=True)

        # Recording metadata from an I/O manager:
        # https://docs.dagster.io/concepts/io-management/io-managers#recording-metadata-from-an-io-manager
        context.add_output_metadata({"db": self.db, "table_name": table_name})

    def load_input(self, context: InputContext):
        """
        Define handling when loading the asset by the downstream process.
        """
        # upstream_output.asset_key is the asset key given to the Out that we're loading for
        table_name = context.upstream_output.asset_key.to_python_identifier()

        engine = create_engine(
            f"postgresql://{self.uid}:{self.pwd}"
            f"@{self.server}:{self.port}/{self.db}"
        )

        query = f"SELECT * FROM public.{table_name}"

        df = pandas.read_sql(query, engine)
        return df


class RecentPostgresDataframeIOManager(PostgresDataframeIOManager):
    """
    Persist time-depend asset in timely variable postgres database. Depending
    on the date state this class returns a different partition associated
    with the recent time frame.
    """

    def handle_output(self, context: OutputContext, obj: pandas.DataFrame):
        # Skip handling if the output is empty
        if obj.empty:
            return

        table_name = context.asset_key.to_python_identifier()

        engine = create_engine(
            f"postgresql://{self.uid}:{self.pwd}"
            f"@{self.server}:{self.port}/{self.db}"
        )

        obj.to_sql(table_name, engine, if_exists="append", index=True)

        # Recording metadata from an I/O manager:
        # https://docs.dagster.io/concepts/io-management/io-managers#recording-metadata-from-an-io-manager
        context.add_output_metadata({"db": self.db, "table_name": table_name})

    def load_input(self, context: InputContext):
        # upstream_output.asset_key is the asset key given to the Out that we're loading for
        table_name = context.upstream_output.asset_key.to_python_identifier()

        processed = read_pandas_asset("recent_interval_processor")
        start_date = processed["last_processed_date"].date()
        end_date = processed["current_date"].date()

        engine = create_engine(
            f"postgresql://{self.uid}:{self.pwd}"
            f"@{self.server}:{self.port}/{self.db}"
        )

        query = f"""
            SELECT * FROM public.{table_name}
            WHERE date BETWEEN '{start_date}' AND '{end_date}'
        """
        df = pandas.read_sql(query, engine)
        return df


@io_manager(
    config_schema={
        "uid": StringSource,
        "pwd": StringSource,
        "server": StringSource,
        "db": StringSource,
        "port": StringSource,
    }
)
def postgres_pandas_io_manager(
    init_context: InitResourceContext,
) -> PostgresDataframeIOManager:
    """
    Generate configurable io_manager from class.
    """
    return PostgresDataframeIOManager(
        pwd=init_context.resource_config["pwd"],
        uid=init_context.resource_config["uid"],
        server=init_context.resource_config["server"],
        db=init_context.resource_config["db"],
        port=init_context.resource_config["port"],
    )


@io_manager(
    config_schema={
        "uid": StringSource,
        "pwd": StringSource,
        "server": StringSource,
        "db": StringSource,
        "port": StringSource,
    }
)
def recent_postgres_pandas_io_manager(
    init_context: InitResourceContext,
) -> PostgresDataframeIOManager:
    """
    Generate configurable io_manager from class.
    """
    return RecentPostgresDataframeIOManager(
        pwd=init_context.resource_config["pwd"],
        uid=init_context.resource_config["uid"],
        server=init_context.resource_config["server"],
        db=init_context.resource_config["db"],
        port=init_context.resource_config["port"],
    )
