import mlflow

from typing import List

class CasualtyRegressor(mlflow.pyfunc.PythonModel):

    def __init__(self, preprocessor, model):

        self.preprocessor = preprocessor
        self.model = model
    
    def predict(self, context, model_input: List[str]) -> List[str]:
        
        X = self.preprocessor.transform(model_input)
        
        X = X[self.model.feature_names_]
        
        return self.model.predict(X)