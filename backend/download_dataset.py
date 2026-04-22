import kagglehub
import os
import shutil

# Predefined Kaggle dataset identifiers (CT and X-ray datasets)
DATASET_IDENTIFIERS = [
    "andrewmvd/covid19-ct-scans",
    "mateuszbuda/lgg-mri-segmentation",
    "nih-chest-xrays/data",
    "pcbreviglieri/pneumonia-xray-images",
]


def dataset_folder_name(dataset_identifier):
    """Build a clear, filesystem-safe folder name from a Kaggle dataset identifier."""
    cleaned = []
    for char in dataset_identifier.lower():
        if char.isalnum():
            cleaned.append(char)
        elif char in {"/", "-", " ", "."}:
            cleaned.append("_")
        # skip any other symbol

    name = "".join(cleaned).strip("_")
    while "__" in name:
        name = name.replace("__", "_")
    return name or "dataset"


def remove_path(path):
    """Remove a file or directory path if it exists."""
    if not os.path.exists(path):
        return

    if os.path.isdir(path):
        shutil.rmtree(path)
    else:
        os.remove(path)


def copy_download_to_target(downloaded_path, target_path):
    """Copy downloaded Kaggle data to the requested target path."""
    if os.path.isdir(downloaded_path):
        shutil.copytree(downloaded_path, target_path)
    else:
        os.makedirs(target_path, exist_ok=True)
        file_name = os.path.basename(downloaded_path)
        shutil.copy2(downloaded_path, os.path.join(target_path, file_name))


def download_datasets(dataset_identifiers):
    """Download each dataset into its own clean subfolder inside ./datasets."""
    base_dir = os.path.join(os.getcwd(), "datasets")
    os.makedirs(base_dir, exist_ok=True)
    print(f"Datasets root: {base_dir}")

    for dataset_identifier in dataset_identifiers:
        subfolder_name = dataset_folder_name(dataset_identifier)
        target_path = os.path.join(base_dir, subfolder_name)

        print("\n" + "=" * 72)
        print(f"Starting download: {dataset_identifier}")
        print(f"Target folder: {target_path}")

        try:
            if os.path.exists(target_path):
                print(f"Existing folder found. Removing: {target_path}")
                remove_path(target_path)

            print("Requesting dataset from Kaggle...")
            downloaded_path = kagglehub.dataset_download(dataset_identifier)
            print(f"Downloaded to cache path: {downloaded_path}")

            print("Copying dataset into target folder...")
            copy_download_to_target(downloaded_path, target_path)

            print(f"Completed: {dataset_identifier}")
        except Exception as exc:
            print(f"Error while processing '{dataset_identifier}': {exc}")
            print("Skipping this dataset and continuing with the next one.")

    print("\nAll dataset download jobs finished.")


if __name__ == "__main__":
    try:
        download_datasets(DATASET_IDENTIFIERS)
    except Exception as exc:
        print(f"Fatal error: {exc}")
