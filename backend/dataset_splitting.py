import pandas as pd
import numpy as np
import os
import shutil
from pathlib import Path
from sklearn.model_selection import train_test_split

# --- Imports and function from 1ZlcAoHP_ehA to ensure preprocessing if not already done ---
from PIL import Image, ImageOps
import torchvision.transforms as transforms

def preprocess_dataset_and_save(
    input_root: Path,
    output_root: Path,
    image_size: tuple = (224, 224),
    equalize: bool = False
):
    """
    Processes images from input_root, applies resizing and optional equalization,
    and saves them as new image files to output_root, maintaining the directory structure.
    """
    output_root.mkdir(parents=True, exist_ok=True)
    processed_count = 0
    skipped_count = 0

    pil_resize_transform = transforms.Resize(image_size)

    for dirpath, dirnames, filenames in os.walk(input_root):
        try:
            relative_path = Path(dirpath).relative_to(input_root)
        except ValueError:
            relative_path = Path('.')

        target_dir = output_root / relative_path
        target_dir.mkdir(parents=True, exist_ok=True)

        for filename in filenames:
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')):
                try:
                    img_path = Path(dirpath) / filename
                    img = Image.open(img_path).convert('RGB')
                    img = pil_resize_transform(img)
                    if equalize:
                        img = ImageOps.equalize(img)

                    target_img_path = target_dir / filename
                    img.save(target_img_path)
                    processed_count += 1
                except Exception as e:
                    print(f"Skipping {img_path} due to error: {e}")
                    skipped_count += 1
            else:
                skipped_count += 1
    return processed_count, skipped_count
# --- End of preprocessing function from 1ZlcAoHP_ehA ---


# --- 1. Define Paths and Ratios ---
# Path to the preprocessed NIH dataset (output of cell 1ZlcAoHP_ehA)
preprocessed_nih_path = Path("/content/NIH_Chest_Xrays_Preprocessed")
# Path to the original NIH dataset (output of cell o2k0jrq2-6jZ) for CSV label extraction
original_nih_path = Path("/content/NIH_Chest_Xrays_Dataset")

# Ensure preprocessing is done if the directory doesn't exist
# This ensures that the dataset splitting can proceed even if 1ZlcAoHP_ehA was not run.
if not preprocessed_nih_path.exists():
    print(f"Preprocessing directory {preprocessed_nih_path} not found. Running preprocessing now...")
    # These variables are expected to be available from previous cells/kernel state
    # 'target_dataset_path' is '/content/NIH_Chest_Xrays_Dataset' from o2k0jrq2-6jZ
    # 'IMG_SIZE' is 224 from kernel state
    # 'equalize=True' is the default from 1ZlcAoHP_ehA

    # Check if target_dataset_path is available from the kernel state
    if 'target_dataset_path' not in globals():
        raise RuntimeError("Error: 'target_dataset_path' not found. Please ensure the dataset download cell (o2k0jrq2-6jZ) has been executed.")
    if 'IMG_SIZE' not in globals():
        # If IMG_SIZE is not set, use a default value for preprocessing
        print("Warning: 'IMG_SIZE' not found in kernel state. Using default 224 for preprocessing.")
        current_img_size = 224
    else:
        current_img_size = IMG_SIZE

    processed_nih, skipped_nih = preprocess_dataset_and_save(
        input_root=Path(target_dataset_path), # Using 'target_dataset_path' from kernel state
        output_root=preprocessed_nih_path,
        image_size=(current_img_size, current_img_size),
        equalize=True # Replicating 1ZlcAoHP_ehA's equalization
    )
    print(f"Preprocessing completed. Processed: {processed_nih}, Skipped: {skipped_nih}")

# Output directory for the split dataset
split_output_base_path = Path("/content/datasplitting") # Modified to 'datasplitting'

TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

# Ensure the preprocessed data path exists (after attempting to create it)
if not preprocessed_nih_path.exists():
    raise FileNotFoundError(f"Preprocessed NIH dataset not found at {preprocessed_nih_path} even after attempting to create it.")
if not original_nih_path.exists():
    raise FileNotFoundError(f"Original NIH dataset not found at {original_nih_path}. "
                            "Please ensure the dataset download cell (o2k0jrq2-6jZ) has been executed.")

# Clean up previous splits if they exist
if split_output_base_path.exists():
    print(f"Removing existing split directory: {split_output_base_path}")
    shutil.rmtree(split_output_base_path)
split_output_base_path.mkdir(parents=True, exist_ok=True)

# --- 2. Load Original Labels ---
# The NIH dataset comes with a CSV file containing image labels
labels_csv_path = original_nih_path / "Data_Entry_2017.csv"
if not labels_csv_path.exists():
    # Try alternative common path for the CSV within the dataset structure
    labels_csv_path = original_nih_path / "NIH-Chest-X-rays" / "Data_Entry_2017.csv"
    if not labels_csv_path.exists():
        raise FileNotFoundError(f"Labels CSV not found at expected paths: {original_nih_path / 'Data_Entry_2017.csv'} or {labels_csv_path}")

df_labels = pd.read_csv(labels_csv_path)

# --- 3. Define Label Mapping Strategy ---
# User-defined diseases + 1 Normal class
user_classes = {
    'NORMAL': ['No Finding'],
    'LUNG OPACITY': ['Atelectasis'], # Mapped Atelectasis
    'COVID': [], # No direct NIH finding
    'PNEUMONIA': ['Viral Pneumonia', 'Bacterial Pneumonia', 'Infiltration', 'Consolidation'],
    'PLEURAL EFFUSION': ['Effusion', 'Pleural_Thickening'],
    'LUNG CANCER': ['Mass', 'Nodule'],
    'PNEUMOTHORAX': ['Pneumothorax'],
    'EMPHYSEMA': ['Emphysema'],
    'PULMONARY FIBROSIS': ['Fibrosis'],
    'SARS': [], # No direct NIH finding
    'MARS': [], # Adding MARS back, no direct NIH finding
    'TUBERCULOSIS': [], # No direct NIH finding
    'LUNG INFECTION': ['Edema'] # Mapped Edema
}

# Create a reverse mapping for quick lookup
reverse_mapping = {}
for user_class, nih_findings in user_classes.items():
    for finding in nih_findings:
        # Prioritize single specific NIH finding to user class mapping
        # If multiple NIH findings map to the same user class, this will handle it.
        reverse_mapping[finding] = user_class

# Function to get the primary standardized label
def get_primary_standard_label(finding_labels_str):
    labels = finding_labels_str.split('|')

    # Prioritize 'No Finding' for 'NORMAL' class
    if 'No Finding' in labels:
        return 'NORMAL'

    # Iterate through labels and map to a user-defined disease
    for label in labels:
        if label in reverse_mapping:
            return reverse_mapping[label]

    # If no specific disease from the user's list is found for disease-labeled images,
    # or if the label is one of the findings not directly listed by user (e.g., Cardiomegaly, Hernia)
    # return a special tag for unmapped/excluded. We will filter these out later.
    return '__UNMAPPED__'

df_labels['standardized_label'] = df_labels['Finding Labels'].apply(get_primary_standard_label)

# Filter out images that could not be mapped to the specified classes
df_filtered = df_labels[df_labels['standardized_label'] != '__UNMAPPED__'].copy()

print(f"Original images: {len(df_labels)}")
print(f"Images mapped to one of the {len(user_classes)} specified classes: {len(df_filtered)}")
print("Distribution of standardized labels:")
print(df_filtered['standardized_label'].value_counts())

# --- 4. Collect Preprocessed Image Paths and Merge with Labels ---
image_data = []
# Assuming preprocessed images are in a structure like /content/NIH_Chest_Xrays_Preprocessed/images/image_name.png
# or if the original structure was flattened, directly under /content/NIH_Chest_Xrays_Preprocessed/

# Need to find the actual directory where preprocessed images are stored
# From cell 1ZlcAoHP_ehA, output is Path("/content/NIH_Chest_Xrays_Preprocessed")
# and it preserves the original relative path, so it should be preprocessed_nih_path / 'images' / ...

# Let's verify the actual image folder, it is usually `images` folder within the `nih_output_path`
# Example: /content/NIH_Chest_Xrays_Preprocessed/images_001/images/00000001_000.png
# or /content/NIH_Chest_Xrays_Preprocessed/images/00000001_000.png

# Try to find the root folder for images in the preprocessed path
image_root_in_preprocessed = None
for root, dirs, files in os.walk(preprocessed_nih_path):
    if any(f.lower().endswith(('.png', '.jpg', '.jpeg')) for f in files):
        image_root_in_preprocessed = Path(root)
        break

if image_root_in_preprocessed is None:
    raise FileNotFoundError(f"Could not find image files within {preprocessed_nih_path}. "
                            "Check the structure of the preprocessed dataset.")

# Adjust preprocessed_nih_path to point to the actual image directory
preprocessed_images_base_path = image_root_in_preprocessed


for image_path in preprocessed_images_base_path.rglob('*.png'): # Assuming .png as preprocessed output
    image_index = image_path.name # Filename is Image Index
    image_data.append({'Image Index': image_index, 'processed_image_path': str(image_path)})

df_processed_images = pd.DataFrame(image_data)

# Merge labels with processed image paths
df_final = pd.merge(df_processed_images, df_filtered, on='Image Index', how='inner')

print(f"Total images after filtering and merging: {len(df_final)}")
print("Final distribution of classes after mapping and filtering:")
print(df_final['standardized_label'].value_counts())

# --- 5. Perform Stratified Train-Validation-Test Split ---
# First split: Train vs (Validation + Test)
X = df_final['processed_image_path']
y = df_final['standardized_label']

X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=(VAL_RATIO + TEST_RATIO), stratify=y, random_state=42)

# Second split: Validation vs Test
X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=(TEST_RATIO / (VAL_RATIO + TEST_RATIO)), stratify=y_temp, random_state=42)

# Create DataFrames for each split
df_train = pd.DataFrame({'processed_image_path': X_train, 'standardized_label': y_train})
df_val = pd.DataFrame({'processed_image_path': X_val, 'standardized_label': y_val})
df_test = pd.DataFrame({'processed_image_path': X_test, 'standardized_label': y_test})

print(f"\nTrain set size: {len(df_train)}")
print(f"Validation set size: {len(df_val)}")
print(f"Test set size: {len(df_test)}")

# --- 6. Create Directory Structure and Copy Images ---
def copy_images_to_splits(df_split, split_name):
    split_dir = split_output_base_path / split_name
    print(f"Creating {split_name} directories and copying images...")
    for idx, row in df_split.iterrows():
        label_dir = split_dir / row['standardized_label']
        label_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(row['processed_image_path'], label_dir / Path(row['processed_image_path']).name)

copy_images_to_splits(df_train, 'train')
copy_images_to_splits(df_val, 'validation')
copy_images_to_splits(df_test, 'test')

print(f"\nDataset splitting complete. Data saved to: {split_output_base_path}")

# Print final counts per class in each split for verification
print("\nClass distribution in Training set:")
print(df_train['standardized_label'].value_counts())
print("\nClass distribution in Validation set:")
print(df_val['standardized_label'].value_counts())
print("\nClass distribution in Test set:")
print(df_test['standardized_label'].value_counts())
