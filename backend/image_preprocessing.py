import os
import shutil
from pathlib import Path
from PIL import Image, ImageOps
import torchvision.transforms as transforms

# Assuming target_dataset_path is available from previous cell execution
# target_dataset_path = "/content/NIH_Chest_Xrays_Dataset"

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

    # Define the transforms that result in a PIL Image
    pil_resize_transform = transforms.Resize(image_size)

    for dirpath, dirnames, filenames in os.walk(input_root):
        # Construct relative path from input_root to current dirpath
        try:
            relative_path = Path(dirpath).relative_to(input_root)
        except ValueError:
            # If dirpath is not a child of input_root (e.g., if input_root is a file),
            # handle it by setting relative_path to an empty path.
            relative_path = Path('.')

        target_dir = output_root / relative_path
        target_dir.mkdir(parents=True, exist_ok=True)

        for filename in filenames:
            # Process only common image file types
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')):
                try:
                    img_path = Path(dirpath) / filename
                    # Open image and convert to RGB to handle various input formats consistently
                    img = Image.open(img_path).convert('RGB')

                    # Apply resizing transform
                    img = pil_resize_transform(img)

                    # Apply histogram equalization if requested
                    if equalize:
                        img = ImageOps.equalize(img)

                    target_img_path = target_dir / filename
                    img.save(target_img_path) # Save the processed PIL image
                    processed_count += 1
                except Exception as e:
                    print(f"Skipping {img_path} due to error: {e}")
                    skipped_count += 1
            else:
                skipped_count += 1
    return processed_count, skipped_count

# --- Apply preprocessing to the NIH Chest X-rays dataset ---
# The variable 'target_dataset_path' should be available from the execution of cell o2k0jrq2-6jZ

if 'target_dataset_path' in globals():
    nih_input_path = Path(target_dataset_path)
    nih_output_path = Path("/content/NIH_Chest_Xrays_Preprocessed")

    print(f"\nApplying preprocessing to NIH Chest X-rays dataset and saving to: {nih_output_path}")

    IMG_SIZE = 224 # Set image size, consistent with common model input requirements

    # Clean up previous data from target directory to ensure a clean run
    if nih_output_path.exists():
        print(f"Removing existing directory: {nih_output_path}")
        shutil.rmtree(nih_output_path)

    processed_nih, skipped_nih = preprocess_dataset_and_save(
        input_root=nih_input_path,
        output_root=nih_output_path,
        image_size=(IMG_SIZE, IMG_SIZE),
        equalize=True # Apply equalization
    )

    print(f"NIH Image preprocessing complete. Processed: {processed_nih}, Skipped: {skipped_nih}")
    print(f"Preprocessed NIH Chest X-rays images saved to: {nih_output_path}")

    # Make the path to the preprocessed NIH dataset available for subsequent cells
    path_nih_preprocessed = nih_output_path
else:
    print("Error: 'target_dataset_path' for NIH dataset not found. Please ensure the dataset download cell (o2k0jrq2-6jZ) is executed.")