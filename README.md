# Project accident-severity-forecast

Create ML models to forecast the severity of accidents based on UK Road Safety Data

## Introduction

This project is aiming to represent an end-to-end machine learning use case including

- **Data ingestion**: Load (partitioned) data from the web and store it in datalake that mimics _AWS S3 service_.
- **Model training**: Provide training environment for running training manually, i.e. in a _Jupyter_ environment, as well as running by the workflow orchestrator. Also account for experiment tracking and model registration.
- **Model serving**: Creation of docker images and provision of an inference web server containing a prediction functionality.
- **Model monitoring**: Continuous tracking of model performance and presentation in dashboards.

## Dataset

The [UK Road Safety Dataset](https://www.data.gov.uk/dataset/cb7ae6f0-4be6-4935-9277-47e5ce24a11f/road-safety-data), is a dataset maintained by the Department for Transport. It provides detailed data on personal injury road accidents in GB from 1979, the vehicles involved, and the resulting casualties. The dataset is divided into Accident, Casualty, and Vehicle information, offering insights into accident severity, environmental conditions, individual demographics, and vehicle details. This dataset is useful for road safety studies, accident analysis, prevention measures, and machine learning model development.

For our project, we utilize data starting from 2016, which contains accident-specific characteristics. This data is suitable for training a machine learning model that may have the potential to be used within a live service to indicate dangerous traffic situations. For this _POC_ project, for the sake of simplicity, we will stick to a _batch_ mode for deployment and monitoring.

## Project outline

The project is decomposed into different _scenarios_, that in real-world applications are handled by different processes.

- **ingestion**: Using [dagster](https://dagster.io/) as generic workflow orchestrator, to download raw data, applying merging of different data tables
  and preprocessing to carry out all the steps to be able to train a machine learning model on this data. Since the raw data is partitioned into yearly
  intervals, we make use of the partitioning the data into so called [partitioned data assets](https://dagster.io/blog/partitioned-data-pipelines).

- **training-manual**: After sucessful data **ingestion**, we can use it to train a machine learning model. Thereby a [jupyterlab](https://jupyterlab.readthedocs.io/en/latest/) environment is created, in which a training notebook can be ran manually. Also an [MLflow](https://mlflow.org/) instance
  is created for logging model metrics and register trained models. The step _training_manual_ is not strictly required as part of the workflow pipeline, however, it is suitable to familarize with the model and its properties.

- **training-workflow**: Since we want to automatically run training by the workflow orchestrator, we make use of [dagstermill](https://docs.dagster.io/_apidocs/libraries/dagstermill), a dagster integration of [papermill](https://papermill.readthedocs.io/en/latest/) to run notebooks in a process while transfering parameters to the notebook. Doing so, you do not have to transfer the code created inside of training notebooks to particular module, and instead just connect the existing notebooks to the pipeline.

- **simulation**: The simulation mode represents a real-world machine learning in production environment. Of course, for our use case the data is available on a yearly basis, so there is no data streaming process appliable. Instead we simulate continuously produced data from the already _ingested_ data and run the processing workflows on a minute-wise schedule. Of course, in the real-world scenario new events, i.e. accidents, occur on a daily basis, but I guess you do not want to wait for days testing the _simulation_ model, do you? :wink:
  To overcome this, we provide a **time warp** mode, where a day is represented by few real-world seconds. Also the simulation start date is synthetic. Both the parameters `SECONDS_PER_DAY` and `SIMULATION_START_DATE`, respectively, can be configured by environment variables.
  The simulation mode requires data **ingestion** and **training** to be completed.

## Quickstart

# Further documention

Take note of further documentation material:

- Process & tooling documentation
- Software architecture
