import os
from sqlalchemy import create_engine, inspect, text


def reinitialize_db():
    """
    Reinintialize database by removing all tables inside associcate with
    recent data.
    """

    server = os.environ["POSTGRES_INFERENCE_SERVER"]
    uid = os.environ["POSTGRES_INFERENCE_USER"]
    db = os.environ["POSTGRES_INFERENCE_DB"]
    pwd = os.environ["POSTGRES_INFERENCE_PASSWORD"]
    port = os.environ["POSTGRES_INFERENCE_PORT"]

    url = f"postgresql://{uid}:{pwd}@{server}:{port}/{db}"
    engine = create_engine(url)

    table_names = inspect(engine).get_table_names()
    conn = engine.connect()
    for table_name in table_names:
        if "recent" in table_name:
            conn.execute(text(f"DROP TABLE IF EXISTS public.{table_name};"))
            conn.commit()
    conn.close()


if __name__ == "__main__":
    reinitialize_db()
