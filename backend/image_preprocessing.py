from __future__ import annotations

import argparse
import logging
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    Image = None
    ImageOps = None


VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def preprocess_image(
    input_path: Path,
    output_path: Path,
    size: tuple[int, int] = (224, 224),
    equalize: bool = True,
) -> None:
    """Preprocess a single image and save it to output_path.

    Steps:
    1) Ensure image is RGB.
    2) Apply optional histogram equalization to improve contrast.
    3) Resize to target size.
    """
    if Image is None:
        logging.warning(f"PIL not installed, skipping preprocessing for {input_path}")
        return
    with Image.open(input_path) as image:
        image = image.convert("L")

        if equalize:
            image = ImageOps.equalize(image)

        image = image.resize(size, Image.Resampling.LANCZOS)
        image = image.convert("RGB")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path)


def preprocess_dataset(
    input_root: str | Path,
    output_root: str | Path,
    size: tuple[int, int] = (224, 224),
    equalize: bool = True,
) -> tuple[int, int]:
    """Preprocess an image dataset while preserving directory structure.

    Returns:
        (processed_count, skipped_count)
    """
    input_root = Path(input_root)
    output_root = Path(output_root)

    if not input_root.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_root}")

    processed_count = 0
    skipped_count = 0

    for path in input_root.rglob("*"):
        if not path.is_file():
            continue

        if path.suffix.lower() not in VALID_EXTENSIONS:
            skipped_count += 1
            continue

        relative = path.relative_to(input_root)
        destination = output_root / relative

        try:
            preprocess_image(
                input_path=path,
                output_path=destination,
                size=size,
                equalize=equalize,
            )
            processed_count += 1
        except OSError:
            skipped_count += 1

    return processed_count, skipped_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preprocess X-ray image datasets.")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("/content/lung_detection"),
        help="Path to dataset root (supports nested train/val/test/class folders).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("/content/Preprocess_data"),
        help="Path where preprocessed images are written.",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=224,
        help="Output image width.",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=224,
        help="Output image height.",
    )
    parser.add_argument(
        "--no-equalize",
        action="store_true",
        help="Disable histogram equalization.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    processed, skipped = preprocess_dataset(
        input_root=args.input_dir,
        output_root=args.output_dir,
        size=(args.width, args.height),
        equalize=not args.no_equalize,
    )
    print(f"Preprocessing complete. Processed: {processed}, Skipped: {skipped}")
    print(f"Output directory: {args.output_dir}")


if __name__ == "__main__":
    main()
