import os
import zipfile
import logging
import shutil
import kagglehub
from utils import ensure_dir, setup_logging

setup_logging()

# List of datasets to download
DATASETS = {
    "covid": "tawsifurrahman/covid19-radiography-database",
    "nih": "nih-chest-xrays/data",
    "lung_disease": "omkarmanohardalvi/lungs-disease-dataset-4-types",
    "sars_mers": "yazanqiblawey/sars-mers-xray-images-dataset"
}

DATASETS_DIR = "/datasets/"

def download_dataset(dataset_id, target_dir):
    try:
        logging.info(f"Downloading {dataset_id} using kagglehub...")
        path = kagglehub.dataset_download(dataset_id)
        logging.info(f"Successfully downloaded to {path}")
        
        # Move files to target_dir if they are not already there
        if os.path.abspath(path) != os.path.abspath(target_dir):
            if os.path.isdir(path):
                for item in os.listdir(path):
                    s = os.path.join(path, item)
                    d = os.path.join(target_dir, item)
                    if os.path.isdir(s):
                        if os.path.exists(d):
                            shutil.rmtree(d)
                        shutil.copytree(s, d)
                    else:
                        shutil.copy2(s, d)
            else:
                shutil.copy2(path, target_dir)
            logging.info(f"Moved files to {target_dir}")
            
        logging.info(f"Successfully integrated {dataset_id}")
    except Exception as e:
        logging.error(f"Error downloading {dataset_id} with kagglehub: {e}")
        logging.info("Falling back to kaggle API...")
        try:
            import kaggle
            kaggle.api.dataset_download_files(dataset_id, path=target_dir, unzip=True)
            logging.info(f"Successfully downloaded and extracted {dataset_id} using kaggle API")
        except Exception as e2:
            logging.error(f"Error downloading {dataset_id} with kaggle API: {e2}")
            logging.info("Make sure you have kaggle.json in ~/.kaggle/kaggle.json")

def main():
    ensure_dir(DATASETS_DIR)
    
    # Check for kaggle.json
    kaggle_path = os.path.expanduser("~/.kaggle/kaggle.json")
    if not os.path.exists(kaggle_path):
        logging.warning(f"Kaggle API key not found at {kaggle_path}. Please upload it.")
        # In a real environment, we'd stop here. For now, we'll just log it.
    
    for name, dataset_id in DATASETS.items():
        # Note: NIH is 45GB, might want to skip it if disk space is low
        if name == "nih":
            logging.info("Skipping NIH dataset (45GB) by default to save space. Modify download.py to enable.")
            continue
        
        target = os.path.join(DATASETS_DIR, name)
        ensure_dir(target)
        download_dataset(dataset_id, target)

if __name__ == "__main__":
    main()
