import os
import torch
from torch.utils.data import DataLoader
from torchvision import datasets, transforms


IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def build_transforms(image_size=(224, 224), mean=IMAGENET_MEAN, std=IMAGENET_STD):
    """Create train/eval transforms for image classification."""
    train_transform = transforms.Compose(
        [
            transforms.Resize(image_size),
            transforms.ToTensor(),
            transforms.Normalize(mean=mean, std=std),
        ]
    )

    eval_transform = transforms.Compose(
        [
            transforms.Resize(image_size),
            transforms.ToTensor(),
            transforms.Normalize(mean=mean, std=std),
        ]
    )

    return train_transform, eval_transform


def create_loader(dataset, batch_size, shuffle, num_workers, pin_memory):
    """Build DataLoader with efficient defaults for CPU/GPU training."""
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        pin_memory=pin_memory,
        persistent_workers=num_workers > 0,
    )


def get_dataloaders(
    data_dir,
    batch_size=32,
    image_size=(224, 224),
    num_workers=4,
    mean=IMAGENET_MEAN,
    std=IMAGENET_STD,
):
    """
    Create PyTorch DataLoaders for train/val/test folders.

    Expected directory structure:
      data_dir/
        train/<class_name>/*
        val/<class_name>/*
        test/<class_name>/*

    Returns:
      train_loader, val_loader, test_loader, class_names
    """
    train_dir = os.path.join(data_dir, "train")
    val_dir = os.path.join(data_dir, "val")
    test_dir = os.path.join(data_dir, "test")

    for split_name, split_dir in (("train", train_dir), ("val", val_dir), ("test", test_dir)):
        if not os.path.isdir(split_dir):
            raise FileNotFoundError(f"Missing '{split_name}' directory: {split_dir}")

    train_transform, eval_transform = build_transforms(
        image_size=image_size,
        mean=mean,
        std=std,
    )

    train_dataset = datasets.ImageFolder(train_dir, transform=train_transform)
    val_dataset = datasets.ImageFolder(val_dir, transform=eval_transform)
    test_dataset = datasets.ImageFolder(test_dir, transform=eval_transform)

    # GPU compatibility: pin_memory improves host->GPU transfer speed when CUDA is available.
    pin_memory = torch.cuda.is_available()

    train_loader = create_loader(
        dataset=train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=pin_memory,
    )
    val_loader = create_loader(
        dataset=val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=pin_memory,
    )
    test_loader = create_loader(
        dataset=test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=pin_memory,
    )

    class_names = train_dataset.classes
    if class_names != val_dataset.classes or class_names != test_dataset.classes:
        raise ValueError("Class mismatch across train/val/test folders")

    return train_loader, val_loader, test_loader, class_names


if __name__ == "__main__":
    # Example usage
    DATA_DIR = "datasets_split"

    try:
        train_loader, val_loader, test_loader, classes = get_dataloaders(
            data_dir=DATA_DIR,
            batch_size=32,
            image_size=(224, 224),
            num_workers=4,
        )
        print(f"Classes: {classes}")
        print(f"Train batches: {len(train_loader)}")
        print(f"Val batches: {len(val_loader)}")
        print(f"Test batches: {len(test_loader)}")
    except Exception as error:
        print(f"Failed to create DataLoaders: {error}")
