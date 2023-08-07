# Project accident-severity-forecast

Create ML models to forecast the severity of accidents based on UK Road Safety Data

## Introduction

This project is aiming to represent an end-to-end machine learning use case including

- **Data ingestion**: Load (partitioned) data from the web and store it in datalake that mimics **AWS S3 service**.
- **Model training**: Provide training environment for running training manually, i.e. in a **Jupyter** environment, as well as running by the workflow orchestrator. Also account for experiment tracking and model registration.
- **Model serving**: Creation of docker images and provision of an inference web server containing a prediction functionality.
- **Model monitoring**: Continuous tracking of model performance and presentation in dashboards.

## Dataset

The Road Safety Dataset, available on data.gov.uk, is a comprehensive collection of data related to road safety in the United Kingdom. This dataset is maintained by the Department for Transport, UK.

The dataset provides detailed information about the circumstances of personal injury road accidents in GB from 1979, the types of vehicles involved, and the consequential casualties. The statistics relate only to personal injury accidents on public roads that are reported to the police and subsequently recorded, using the STATS19 accident reporting form.

The dataset is divided into three main sections:

- **Accident Information**: This includes details about the severity of the accident, number of vehicles involved, date, time, location, and other environmental conditions.

- **Casualty Information**: This section provides data about the individuals involved in the accident, including age, gender, type of road user, and the severity of their injuries.

- **Vehicle Information**: This part of the dataset includes information about the vehicles involved in the accident, such as the type of vehicle, the manoeuvre the vehicle was performing at the time of the accident, and the age and gender of the driver.

This dataset is a valuable resource for anyone interested in studying road safety, accident analysis, and prevention measures. It can also be used to develop machine learning models for predicting accident severity based on various factors.

## Project outline

## Quickstart
