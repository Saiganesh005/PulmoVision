import kagglehub
import os
import shutil

# Define the target directory in /content
target_dataset_path = "/content/NIH_Chest_Xrays_Dataset"

print("Downloading NIH Chest X-rays dataset...")

# Download latest version of the dataset
# This downloads to the KaggleHub cache directory
downloaded_path = kagglehub.dataset_download("nih-chest-xrays/data")

print(f"Dataset initially downloaded to: {downloaded_path}")

# Ensure the target directory for moving exists
if os.path.exists(target_dataset_path):
    print(f"Removing existing directory: {target_dataset_path}")
    shutil.rmtree(target_dataset_path)

# Move the downloaded dataset to the target path in /content
# shutil.move handles moving files/directories across different file systems
print(f"Moving dataset from {downloaded_path} to {target_dataset_path}...")
shutil.move(downloaded_path, target_dataset_path)

print(f"NIH Chest X-rays dataset is now available at: {target_dataset_path}")

# Update the 'path' variable to reflect the final location
path = target_dataset_path