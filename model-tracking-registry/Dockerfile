FROM python:3.11-slim

RUN pip install PyMySQL && \   
    pip install psycopg2-binary && \
    pip install mlflow[extras]

ENTRYPOINT ["mlflow", "server", "--host", "0.0.0.0"]