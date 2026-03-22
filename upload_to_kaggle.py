import os
import logging
import kagglehub
from utils import setup_logging

setup_logging()

def upload_model(model_path, handle, description="Trained medical image classification model"):
    try:
        logging.info(f"Uploading model from {model_path} to Kaggle Hub: {handle}...")
        # handle format: username/model-name/pytorch/version-name
        kagglehub.model_upload(handle, model_path, license_name="Apache 2.0", description=description)
        logging.info(f"Successfully uploaded model to {handle}")
    except Exception as e:
        logging.error(f"Error uploading model to Kaggle Hub: {e}")

if __name__ == "__main__":
    # Example: Upload the model
    model_path = "/outputs/model.pth"
    # Replace with your Kaggle username and model name
    handle = "your-username/medical-xray-classifier/pytorch/v1"
    
    if os.path.exists(model_path):
        logging.info("To upload, please modify upload_to_kaggle.py with your handle and run it.")
        # upload_model(model_path, handle)
    else:
        logging.warning(f"Model file {model_path} not found. Skip upload.")
