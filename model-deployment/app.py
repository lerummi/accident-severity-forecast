import os
import mlflow
import json
from fastapi import FastAPI, HTTPException, Request, Response

app = FastAPI()

# Load the MLflow model during app startup
model_name = os.environ["MODEL_NAME"]
model_version = os.environ["MODEL_VERSION"]
model_path = f"models:/{model_name}/{model_version}"
loaded_model = None


@app.on_event("startup")
async def load_model():
    global loaded_model
    loaded_model = mlflow.pyfunc.load_model(model_path)


@app.post("/predict/")
async def predict(request: Request):
    if loaded_model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")

    try:
        data = await request.json()
        # Assuming your model expects the input data in a specific format, adjust accordingly
        predictions = loaded_model.predict(data)
        return {"predictions": predictions}
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