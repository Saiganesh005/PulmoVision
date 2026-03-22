import sys
import json
import argparse
import logging
import subprocess
import os

def install_package(package):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--user", "--no-cache-dir"])
    except Exception as e:
        pass

# Try to import kaggle API
try:
    from kaggle.api.kaggle_api_extended import KaggleApi
    HAS_KAGGLE_API = True
except ImportError:
    install_package("kaggle")
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        HAS_KAGGLE_API = True
    except ImportError:
        HAS_KAGGLE_API = False

def search_datasets(query):
    # Mock results as fallback
    popular = [
        {
            "name": "Covid 19 Radiography Dataset", 
            "id": "tawsifurrahman/covid19-radiography-database", 
            "size": "806.84 MB", 
            "images": "21,165", 
            "isLarge": False,
            "description": "A database of chest X-ray images for COVID-19 positive cases along with Normal and Viral Pneumonia images."
        },
        {
            "name": "NIH Chest X-ray Dataset", 
            "id": "nih-chest-xrays/data", 
            "size": "45.08 GB", 
            "images": "112,120", 
            "isLarge": True,
            "description": "ChestX-ray14 dataset comprises 112,120 frontal-view X-ray images of 30,805 unique patients."
        },
        {
            "name": "Lung Disease Dataset", 
            "id": "omkarmanohardalvi/lungs-disease-dataset-4-types", 
            "size": "2.23 GB", 
            "images": "6,054", 
            "isLarge": True,
            "description": "This dataset contains 6054 images of 4 types of lung diseases: Covid-19, Normal, Viral Pneumonia, and Bacterial Pneumonia."
        }
    ]

    if not HAS_KAGGLE_API:
        return popular

    try:
        # Initialize and authenticate
        api = KaggleApi()
        api.authenticate()
        
        # Search for datasets
        # dataset_list(search=query) returns a list of Dataset objects
        datasets = api.dataset_list(search=query)
        
        if not datasets:
            return popular
            
        results = []
        for ds in datasets:
            results.append({
                "name": str(ds.title),
                "id": str(ds.ref),
                "size": str(ds.size),
                "images": "N/A",
                "isLarge": "GB" in str(ds.size),
                "description": str(getattr(ds, 'description', ''))
            })
        
        return results
        
    except Exception as e:
        # Fallback to mock if API fails (likely due to auth)
        sys.stderr.write(f"DEBUG: Kaggle API Search failed: {str(e)}\n")
        return popular

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", type=str, default="")
    args = parser.parse_args()
    
    results = search_datasets(args.query)
    print(json.dumps(results))
