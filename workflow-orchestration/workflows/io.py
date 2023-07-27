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

    def _get_path(self, output_context):
        return os.path.join(
            self._base_dir,
            f"{output_context.step_key}_{output_context.name}.pkl",
        )

    def handle_output(self, context, obj: pandas.DataFrame):
        file_path = self._get_path(context)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        if obj is not None:
            obj.to_pickle(file_path)

    def load_input(self, context) -> pandas.DataFrame:
        return pandas.read_pickle(self._get_path(context.upstream_output))
    