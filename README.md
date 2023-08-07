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

## Quickstart
