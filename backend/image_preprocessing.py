import os
import cv2
import numpy as np


SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}


def ensure_clean_output_folder(output_root: str, remove_existing: bool = False) -> None:
    """Create output folder, optionally removing existing files first."""
    if remove_existing and os.path.isdir(output_root):
        for dirpath, dirnames, filenames in os.walk(output_root, topdown=False):
            for filename in filenames:
                os.remove(os.path.join(dirpath, filename))
            for dirname in dirnames:
                os.rmdir(os.path.join(dirpath, dirname))
    os.makedirs(output_root, exist_ok=True)


def normalize_to_uint8(image: np.ndarray) -> np.ndarray:
    """Normalize image to [0, 1] and convert back to uint8 for saving."""
    image_float = image.astype(np.float32) / 255.0
    return np.clip(image_float * 255.0, 0, 255).astype(np.uint8)


def preprocess_ct_image(image: np.ndarray, use_clahe: bool = False) -> np.ndarray:
    """CT preprocessing: grayscale, resize, normalize, optional CLAHE."""
    if image is None:
        raise ValueError("Invalid CT image data")

    if image.ndim == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    image = cv2.resize(image, (224, 224), interpolation=cv2.INTER_AREA)

    if use_clahe:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        image = clahe.apply(image)

    return normalize_to_uint8(image)


def preprocess_xray_image(image: np.ndarray) -> np.ndarray:
    """X-ray preprocessing: grayscale, resize, equalize, normalize, 3 channels."""
    if image is None:
        raise ValueError("Invalid X-ray image data")

    if image.ndim == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    image = cv2.resize(image, (224, 224), interpolation=cv2.INTER_AREA)
    image = cv2.equalizeHist(image)
    image = normalize_to_uint8(image)
    image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    return image


def is_supported_image(filename: str) -> bool:
    return os.path.splitext(filename.lower())[1] in SUPPORTED_EXTENSIONS


def process_dataset(
    input_root: str,
    output_root: str,
    image_processor,
    processor_name: str,
    remove_existing_output: bool = False,
    **processor_kwargs,
) -> dict:
    """
    Process a dataset while preserving the input folder structure.

    Args:
        input_root: Source directory containing images in nested folders.
        output_root: Destination directory for processed images.
        image_processor: Function that accepts an image array and returns processed image.
        processor_name: Display name for logging.
        remove_existing_output: If True, clear output directory first.
        processor_kwargs: Optional kwargs passed to image_processor.

    Returns:
        Dictionary with processing stats.
    """
    if not os.path.isdir(input_root):
        raise FileNotFoundError(f"Input folder not found: {input_root}")

    ensure_clean_output_folder(output_root, remove_existing=remove_existing_output)

    processed = 0
    skipped = 0
    failed = 0

    print(f"\n[{processor_name}] Input:  {input_root}")
    print(f"[{processor_name}] Output: {output_root}")

    for dirpath, _, filenames in os.walk(input_root):
        relative_path = os.path.relpath(dirpath, input_root)
        target_dir = output_root if relative_path == "." else os.path.join(output_root, relative_path)
        os.makedirs(target_dir, exist_ok=True)

        for filename in filenames:
            if not is_supported_image(filename):
                skipped += 1
                continue

            input_path = os.path.join(dirpath, filename)
            output_path = os.path.join(target_dir, filename)

            try:
                image = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
                processed_image = image_processor(image, **processor_kwargs)
                saved = cv2.imwrite(output_path, processed_image)
                if not saved:
                    raise IOError(f"Failed to save image: {output_path}")
                processed += 1
            except Exception as error:
                failed += 1
                print(f"[{processor_name}] Error: {input_path} -> {error}")

    stats = {
        "processed": processed,
        "skipped": skipped,
        "failed": failed,
    }
    print(f"[{processor_name}] Done. {stats}")
    return stats


def preprocess_ct_dataset(
    input_root: str,
    output_root: str,
    use_clahe: bool = False,
    remove_existing_output: bool = False,
) -> dict:
    """Preprocess CT scan dataset and preserve nested folder structure."""
    return process_dataset(
        input_root=input_root,
        output_root=output_root,
        image_processor=preprocess_ct_image,
        processor_name="CT",
        remove_existing_output=remove_existing_output,
        use_clahe=use_clahe,
    )


def preprocess_xray_dataset(
    input_root: str,
    output_root: str,
    remove_existing_output: bool = False,
) -> dict:
    """Preprocess chest X-ray dataset and preserve class folder structure."""
    return process_dataset(
        input_root=input_root,
        output_root=output_root,
        image_processor=preprocess_xray_image,
        processor_name="X-RAY",
        remove_existing_output=remove_existing_output,
    )


if __name__ == "__main__":
    # Example paths (update for your environment)
    ct_input_folder = "datasets/ct_scans"
    ct_output_folder = "datasets_preprocessed/ct_scans"

    xray_input_folder = "datasets/chest_xray"
    xray_output_folder = "datasets_preprocessed/chest_xray"

    try:
        preprocess_ct_dataset(
            input_root=ct_input_folder,
            output_root=ct_output_folder,
            use_clahe=True,
            remove_existing_output=False,
        )
    except Exception as error:
        print(f"CT preprocessing failed: {error}")

    try:
        preprocess_xray_dataset(
            input_root=xray_input_folder,
            output_root=xray_output_folder,
            remove_existing_output=False,
        )
    except Exception as error:
        print(f"X-ray preprocessing failed: {error}")
