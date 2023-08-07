FROM python:3.11-slim

# Install apt packages
RUN apt-get update && \
    apt-get install -y git && \
    pip install pip --upgrade && \
    pip install poetry && \
    rm -rf /var/lib/apt/lists/*

# Requirements are installed here to ensure they will be cached.
COPY pyproject.toml pyproject.toml
COPY poetry.lock poetry.lock

WORKDIR /app

# Install Python 3 packages
RUN poetry export -o /tmp/requirements.txt --without-hashes && \
    cat /tmp/requirements.txt

RUN pip install \
    --user \
    --use-deprecated=legacy-resolver \
    -r /tmp/requirements.txt

RUN echo PATH=$PATH:/root/.local/bin >> ~/.bashrc
RUN mkdir -p /opt/mlflow

COPY workflows /app/workflows
COPY start.sh /
RUN chmod +x /start.sh

EXPOSE 8000
