FROM python:3.11-slim

# Set $DAGSTER_HOME and copy dagster instance and workspace YAML there
ENV DAGSTER_HOME=/opt/dagster/dagster_home/


# Install apt packages
RUN apt-get update && \
    apt-get install -y git && \
    apt-get install -y wget && \
    pip install poetry && \
    rm -rf /var/lib/apt/lists/*


# Requirements are installed here to ensure they will be cached.
COPY pyproject.toml pyproject.toml
COPY poetry.lock poetry.lock


# Install Python 3 packages
RUN pip install poetry && \	
    poetry export -o /tmp/requirements.txt --without-hashes && \
    cat /tmp/requirements.txt

RUN pip install --use-deprecated=legacy-resolver  -r /tmp/requirements.txt


# Take care of dagster configuration
RUN mkdir -p $DAGSTER_HOME
COPY workflows $DAGSTER_HOME/workflows
COPY dagster.yaml workspace.yaml $DAGSTER_HOME


WORKDIR $DAGSTER_HOME