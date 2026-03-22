from __future__ import annotations

import argparse
import shutil
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    Image = None

try:
    import kagglehub
except ImportError:
    kagglehub = None

DATASETS: dict[str, str] = {
    "Covid 19 Radiography Dataset": "tawsifurrahman/covid19-radiography-database",
    "NIH Chest X-ray Dataset": "nih-chest-xrays/data",
    "Lung Disease Dataset": "omkarmanohardalvi/lungs-disease-dataset-4-types",
    "SARS & MERS Dataset": "yazanqiblawey/sars-mers-xray-images-dataset",
}

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}


def is_red_highlighted(image_path: Path, threshold: float = 0.015) -> bool:
    """Return True if an image appears to contain red annotation/highlight overlays."""
    if Image is None:
        return False
    with Image.open(image_path) as image:
        rgb_image = image.convert("RGB")
        pixels = rgb_image.getdata()

        highlighted_pixels = 0
        for red, green, blue in pixels:
            if red > 170 and red > (green + 45) and red > (blue + 45):
                highlighted_pixels += 1

    total_pixels = max(rgb_image.size[0] * rgb_image.size[1], 1)
    return (highlighted_pixels / total_pixels) >= threshold


def copy_without_red_highlights(source_dir: Path, output_dir: Path) -> tuple[int, int]:
    """Copy dataset tree to a new directory and skip red-highlighted images."""
    kept = 0
    skipped = 0

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for source_path in source_dir.rglob("*"):
        relative_path = source_path.relative_to(source_dir)
        destination_path = output_dir / relative_path

        if source_path.is_dir():
            destination_path.mkdir(parents=True, exist_ok=True)
            continue

        destination_path.parent.mkdir(parents=True, exist_ok=True)

        if source_path.suffix.lower() in IMAGE_EXTENSIONS:
            if is_red_highlighted(source_path):
                skipped += 1
                continue

        shutil.copy2(source_path, destination_path)
        kept += 1

    return kept, skipped


def download_datasets(remove_red_highlighted: bool = False) -> dict[str, str]:
    """Download all datasets required for MedScanXR and return local paths."""
    if kagglehub is None:
        print("Kagglehub not installed, cannot download datasets.")
        return {}

    downloaded_paths: dict[str, str] = {}

    print("Downloading datasets...")
    for name, handle in DATASETS.items():
        print(f"- {name}")
        dataset_path = Path(kagglehub.dataset_download(handle))

        if remove_red_highlighted:
            clean_path = dataset_path.parent / f"{dataset_path.name}_no_red_highlights"
            kept, skipped = copy_without_red_highlights(dataset_path, clean_path)
            print(f"  cleaned dataset saved to: {clean_path}")
            print(f"  files kept: {kept}, red-highlighted images removed: {skipped}")
            downloaded_paths[name] = str(clean_path)
        else:
            downloaded_paths[name] = str(dataset_path)

    return downloaded_paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download MedScanXR datasets from Kaggle.")
    parser.add_argument(
        "--remove-red-highlighted",
        action="store_true",
        help="Copy downloaded datasets to a cleaned directory and remove red-highlighted images.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    paths = download_datasets(remove_red_highlighted=args.remove_red_highlighted)
    for dataset_name, dataset_path in paths.items():
        print(f"{dataset_name} Path: {dataset_path}")
