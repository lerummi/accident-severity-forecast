import mlflow
import argparse


def save_model_to_local(model_name, model_version, model_flavor, **kwargs):

    # Specify model uri
    model_uri = f"models:/{model_name}/{model_version}"

    # Load model
    loader = getattr(mlflow, model_flavor).load_model
    model = loader(model_uri)

    # Save model to local
    saver = getattr(mlflow, model_flavor).save_model
    saver(model, "/opt/mlflow/model.pkl")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Download molde from MLFlow tracking server and "
                    "store local",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-m", "--model-name", 
        help="Name of registered model"
    )
    parser.add_argument(
        "-v", "--model-version", 
        help="Version of registered model"
        )
    parser.add_argument(
        "-f", "--model-flavor", 
        help="Flavor of registered model"
    )

    args = parser.parse_args()
    save_model_to_local(**vars(args))
