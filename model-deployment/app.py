import os
import json
import mlflow
from typing import List
from fastapi import FastAPI, HTTPException, Response

from models import (
    type_convert,
    input_signature_to_schema,
    Predictions
)

model_name = os.environ["MODEL_NAME"]
model_version = os.environ["MODEL_VERSION"]
model_path = f"models:/{model_name}/{model_version}"

app = FastAPI(
    title="Model inference App",
    description=
        f"Make inference given deployed model: {model_path}"
)

# Load the MLflow model during app startup
loaded_model = mlflow.pyfunc.load_model(model_path)
input_signature = input_signature_to_schema(loaded_model)


@app.post("/predict/")
async def predict(data: List[input_signature]) -> Predictions:
    if loaded_model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")

    try:
        # Convert pydantic model to dict
        data = list(map(dict, data))
        predictions = loaded_model.predict(data)
        return {"predictions": list(predictions)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@app.get("/info/")
async def get_model_info():
    if loaded_model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")

    try:
        model_info = json.loads(loaded_model.metadata.to_json())
        model_info["model_name"] = model_name
        model_info["model_version"] = model_version
        # Assuming the loaded_model.metadata.to_json() returns a JSON string
        return Response(
            content=json.dumps(model_info),
            media_type="application/json"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail="Failed to retrieve model information"
        )