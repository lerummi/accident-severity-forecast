FROM localstack/localstack:2.2

RUN echo "Upgrading to the latest localstack CLI..."
RUN apt-get update && apt-get install -y gcc \
	&& rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade localstack localstack-ext