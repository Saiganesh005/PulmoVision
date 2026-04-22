import os
import shutil
import random


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}


def is_image_file(filename: str) -> bool:
    """Return True if file extension is a supported image type."""
    return os.path.splitext(filename.lower())[1] in IMAGE_EXTENSIONS


def clear_directory(directory: str) -> None:
    """Delete all files/subfolders in a directory while keeping the directory itself."""
    if not os.path.isdir(directory):
        return

    for entry in os.listdir(directory):
        path = os.path.join(directory, entry)
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)


def collect_class_images(class_dir: str) -> list:
    """
    Collect all image file paths inside a class folder.
    Keeps relative paths so nested structure can be preserved if present.
    """
    image_paths = []
    for root, _, files in os.walk(class_dir):
        for file_name in files:
            if not is_image_file(file_name):
                continue
            full_path = os.path.join(root, file_name)
            relative_path = os.path.relpath(full_path, class_dir)
            image_paths.append(relative_path)
    return image_paths


def split_items(items: list, train_ratio: float, val_ratio: float, test_ratio: float) -> tuple:
    """Split a list into train/val/test partitions by ratio."""
    total = len(items)
    train_count = int(total * train_ratio)
    val_count = int(total * val_ratio)

    train_items = items[:train_count]
    val_items = items[train_count:train_count + val_count]
    test_items = items[train_count + val_count:]

    return train_items, val_items, test_items


def copy_split_files(
    class_name: str,
    source_class_dir: str,
    output_dir: str,
    split_name: str,
    split_files: list,
) -> None:
    """Copy split files into output/<split>/<class>/... while preserving relative paths."""
    for rel_path in split_files:
        src_path = os.path.join(source_class_dir, rel_path)
        dst_path = os.path.join(output_dir, split_name, class_name, rel_path)

        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        shutil.copy2(src_path, dst_path)


def split_dataset(
    input_dir: str,
    output_dir: str,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    seed: int = 42,
    clear_output: bool = True,
) -> dict:
    """
    Split a class-wise image dataset into train/val/test folders.

    Output structure:
      output_dir/
        train/<class_name>/...
        val/<class_name>/...
        test/<class_name>/...
    """
    if not os.path.isdir(input_dir):
        raise FileNotFoundError(f"Input dataset folder not found: {input_dir}")

    ratio_sum = train_ratio + val_ratio + test_ratio
    if abs(ratio_sum - 1.0) > 1e-8:
        raise ValueError("train_ratio + val_ratio + test_ratio must equal 1.0")

    class_names = [
        name for name in os.listdir(input_dir)
        if os.path.isdir(os.path.join(input_dir, name))
    ]
    if not class_names:
        raise ValueError("No class folders found inside input_dir")

    os.makedirs(output_dir, exist_ok=True)
    if clear_output:
        clear_directory(output_dir)

    for split in ("train", "val", "test"):
        os.makedirs(os.path.join(output_dir, split), exist_ok=True)

    random.seed(seed)

    summary = {
        "train": 0,
        "val": 0,
        "test": 0,
        "per_class": {},
    }

    for class_name in sorted(class_names):
        source_class_dir = os.path.join(input_dir, class_name)
        image_rel_paths = collect_class_images(source_class_dir)

        random.shuffle(image_rel_paths)
        train_files, val_files, test_files = split_items(
            image_rel_paths,
            train_ratio=train_ratio,
            val_ratio=val_ratio,
            test_ratio=test_ratio,
        )

        # Avoid leakage: each image appears in exactly one split.
        seen = set(train_files) | set(val_files) | set(test_files)
        if len(seen) != len(image_rel_paths):
            raise RuntimeError(f"Data leakage/duplication detected in class: {class_name}")

        copy_split_files(class_name, source_class_dir, output_dir, "train", train_files)
        copy_split_files(class_name, source_class_dir, output_dir, "val", val_files)
        copy_split_files(class_name, source_class_dir, output_dir, "test", test_files)

        class_counts = {
            "train": len(train_files),
            "val": len(val_files),
            "test": len(test_files),
            "total": len(image_rel_paths),
        }
        summary["per_class"][class_name] = class_counts
        summary["train"] += class_counts["train"]
        summary["val"] += class_counts["val"]
        summary["test"] += class_counts["test"]

        print(
            f"[{class_name}] total={class_counts['total']} | "
            f"train={class_counts['train']} val={class_counts['val']} test={class_counts['test']}"
        )

    print("\nSplit complete.")
    print(f"Train images: {summary['train']}")
    print(f"Val images:   {summary['val']}")
    print(f"Test images:  {summary['test']}")

    return summary


if __name__ == "__main__":
    # Update these paths before running.
    INPUT_DATASET_DIR = "datasets_preprocessed/chest_xray"
    OUTPUT_SPLIT_DIR = "datasets_split"

    try:
        split_dataset(
            input_dir=INPUT_DATASET_DIR,
            output_dir=OUTPUT_SPLIT_DIR,
            train_ratio=0.70,
            val_ratio=0.15,
            test_ratio=0.15,
            seed=42,
            clear_output=True,
        )
    except Exception as exc:
        print(f"Dataset split failed: {exc}")
