FROM python:3.11-slim

ARG MLFLOW_TRACKING_URI=http://0.0.0.0:5000
ARG MODEL_NAME
ARG MODEL_VERSION
ARG MODEL_FLAVOR

ENV MLFLOW_TRACKING_URI=${MLFLOW_TRACKING_URI}

# Install apt packages
RUN apt-get update && \
    apt-get install -y git && \
    pip install pip --upgrade && \
    pip install poetry && \
    rm -rf /var/lib/apt/lists/*

# Requirements are installed here to ensure they will be cached.
COPY pyproject.toml pyproject.toml
COPY poetry.lock poetry.lock

# Install Python 3 packages
RUN poetry export -o /tmp/requirements.txt --without-hashes && \
    cat /tmp/requirements.txt

RUN pip install \
    --user \
    --use-deprecated=legacy-resolver \
    -r /tmp/requirements.txt

RUN echo PATH=$PATH:/root/.local/bin >> ~/.bashrc
RUN mkdir -p /opt/mlflow
COPY download_model.py .
RUN python3 download_model.py -m accident_severity -v 6 -f catboost