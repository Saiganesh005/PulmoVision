import os
import logging
from utils import setup_logging, ensure_dir
from download import main as download_main
from split import main as split_main
from train import train_model
from evaluate import evaluate_model
from inference import predict_image

setup_logging()

def main():
    logging.info("Starting full deep learning pipeline...")
    
    # 1. Download Datasets
    logging.info("Step 1: Downloading datasets...")
    download_main()
    
    # 2. Split Dataset
    logging.info("Step 2: Splitting datasets...")
    split_main()
    
    # 3. Preprocessing & Augmentation (Defined in preprocess.py, used in train.py)
    logging.info("Step 3: Preprocessing and Augmentation defined in preprocess.py.")
    
    # 4. Model Training
    logging.info("Step 4: Training model...")
    data_dir = "/data"
    if os.path.exists(data_dir):
        train_model(data_dir, epochs=5) # Reduced epochs for testing
    else:
        logging.error("Data directory not found. Skipping training.")
        return
    
    # 5. Evaluation
    logging.info("Step 5: Evaluating model...")
    if os.path.exists("/outputs/model.pth"):
        evaluate_model(data_dir)
    else:
        logging.error("Model not found. Skipping evaluation.")
        return
    
    # 6. Inference (Testing)
    logging.info("Step 6: Testing inference...")
    # Find a test image
    test_dir = os.path.join(data_dir, 'test')
    classes = [d for d in os.listdir(test_dir) if os.path.isdir(os.path.join(test_dir, d))]
    if classes:
        first_class = classes[0]
        class_dir = os.path.join(test_dir, first_class)
        images = [f for f in os.listdir(class_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if images:
            test_img = os.path.join(class_dir, images[0])
            logging.info(f"Testing inference on {test_img}...")
            predict_image(test_img, classes=classes)
        else:
            logging.warning("No test images found.")
    else:
        logging.warning("No test classes found.")
    
    logging.info("Full pipeline execution complete. Check /outputs/ for results.")

if __name__ == "__main__":
    main()
