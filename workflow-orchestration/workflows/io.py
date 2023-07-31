import os
import pandas
from pathlib import Path
from dagster import ConfigurableIOManager


data_dir = Path(os.environ["DATA_DIR"])


class PandasIOManager(ConfigurableIOManager):

    @property
    def _base_dir(self):

        base_dir = data_dir / "assets"
        base_dir.mkdir(parents=True, exist_ok=True)
        return str(base_dir)

    def _get_out_path(self, context):
        return os.path.join(
            self._base_dir,
            f"{context.step_key}.parquet",
        )

    def _get_in_path(self, context):
        return os.path.join(
            self._base_dir,
            f"{context.name}.parquet",
        )

    def handle_output(self, context, obj: pandas.DataFrame):
        file_path = self._get_out_path(context)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        if obj is not None:
            obj.to_parquet(file_path)

    def load_input(self, context) -> pandas.DataFrame:
        return pandas.read_parquet(self._get_in_path(context.upstream_output))
    

class PartionedPandasIOManager(ConfigurableIOManager):

    @property
    def _base_dir(self):

        base_dir = data_dir / "assets"
        base_dir.mkdir(parents=True, exist_ok=True)
        return str(base_dir)

    def _get_path(self, context) -> str:

        if context.has_partition_key:
            asset_dir = Path(self._base_dir) / "_".join(context.asset_key.path)
            asset_dir.mkdir(parents=True, exist_ok=True)

            return asset_dir / f"{context.asset_partition_key}.parquet"
        else:
            return os.path.join(
                self._base_dir,
                f"{context.asset_key.path}.parquet"
            )

    def handle_output(self, context, obj: pandas.DataFrame):
        obj.to_parquet(self._get_path(context))

    def load_input(self, context):
        return pandas.read_parquet(self._get_path(context))
    