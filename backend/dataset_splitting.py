from __future__ import annotations

import argparse
import random
import shutil
from pathlib import Path


VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def split_files(
    files: list[Path],
    train_ratio: float,
    val_ratio: float,
) -> tuple[list[Path], list[Path], list[Path]]:
    """Split file list into train/val/test subsets."""
    total = len(files)
    train_end = int(total * train_ratio)
    val_end = train_end + int(total * val_ratio)

    train_files = files[:train_end]
    val_files = files[train_end:val_end]
    test_files = files[val_end:]
    return train_files, val_files, test_files


def split_dataset(
    input_dir: str | Path,
    output_dir: str | Path,
    train_ratio: float = 0.75,
    val_ratio: float = 0.15,
    test_ratio: float = 0.10,
    seed: int = 42,
) -> dict[str, int]:
    """Split a class-folder dataset into train/val/test structure.

    Expects:
      input_dir/
        class_a/
        class_b/
    Produces:
      output_dir/
        train/class_a
        val/class_a
        test/class_a
    """
    if abs((train_ratio + val_ratio + test_ratio) - 1.0) > 1e-9:
        raise ValueError("train_ratio + val_ratio + test_ratio must equal 1.0")

    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    if not input_dir.exists():
        raise FileNotFoundError(f"Input dataset directory not found: {input_dir}")

    class_dirs = [path for path in input_dir.iterdir() if path.is_dir()]
    if not class_dirs:
        raise ValueError(f"No class directories found in: {input_dir}")

    random.seed(seed)

    counts = {"train": 0, "val": 0, "test": 0}

    for class_dir in sorted(class_dirs):
        images = [
            image_path
            for image_path in class_dir.iterdir()
            if image_path.is_file() and image_path.suffix.lower() in VALID_EXTENSIONS
        ]
        random.shuffle(images)

        train_files, val_files, test_files = split_files(images, train_ratio, val_ratio)

        for split_name, split_files_list in {
            "train": train_files,
            "val": val_files,
            "test": test_files,
        }.items():
            split_class_dir = output_dir / split_name / class_dir.name
            split_class_dir.mkdir(parents=True, exist_ok=True)

            for file_path in split_files_list:
                shutil.copy2(file_path, split_class_dir / file_path.name)
                counts[split_name] += 1

    return counts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Split image dataset into train/val/test folders.")
    parser.add_argument(
        "--input-dir",
        type=Path,
        required=True,
        help="Path to dataset root with class subdirectories.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("/content/lung_detection"),
        help="Path where split dataset will be written.",
    )
    parser.add_argument("--train-ratio", type=float, default=0.75)
    parser.add_argument("--val-ratio", type=float, default=0.15)
    parser.add_argument("--test-ratio", type=float, default=0.10)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    counts = split_dataset(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        seed=args.seed,
    )

    print("Dataset splitting complete.")
    print(f"Train images: {counts['train']}")
    print(f"Validation images: {counts['val']}")
    print(f"Test images: {counts['test']}")
    print(f"Output directory: {args.output_dir}")


if __name__ == "__main__":
    main()
