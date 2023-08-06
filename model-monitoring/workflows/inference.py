import os

import pandas
import requests

predict_url = os.environ["PREDICT_URL"]


def make_prediction(X: pandas.DataFrame):
    """
    Given dataset, request predictions against 'predict_url'
    """
    X = X.fillna("nan")

    index = X.pop("accident.accident_index")
    date = X.pop("date")

    headers = {"Content-type": "application/json"}

    response = requests.post(
        predict_url, json=X.to_dict("records"), headers=headers, timeout=30
    )

    if response.status_code != 200:
        raise requests.HTTPError(
            f"Endpoint '{predict_url}' returned "
            f"status code {response.status_code}. Error text: {response.text}."
        )

    predictions = response.json()
    result = pandas.DataFrame.from_dict(predictions)
    result["date"] = date
    result.index = index

    return result
