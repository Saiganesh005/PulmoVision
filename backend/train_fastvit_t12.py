from __future__ import annotations

import argparse
from pathlib import Path

import timm
import torch
import torch.nn as nn
import torch.optim as optim

from dataloader import get_dataloaders


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train FastViT-T12 on MedScanXR dataset")
    parser.add_argument("--data-dir", type=str, default="/content/Preprocess_data")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--save-path", type=Path, default=Path("fastvit_t12_model.pth"))
    return parser.parse_args()


def train_one_epoch(
    model: nn.Module,
    loader: torch.utils.data.DataLoader,
    criterion: nn.Module,
    optimizer: optim.Optimizer,
    device: torch.device,
) -> float:
    model.train()
    running_loss = 0.0

    for images, labels in loader:
        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * images.size(0)

    return running_loss / len(loader.dataset)


def evaluate(
    model: nn.Module,
    loader: torch.utils.data.DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> tuple[float, float]:
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)
            loss = criterion(outputs, labels)

            running_loss += loss.item() * images.size(0)
            predictions = outputs.argmax(dim=1)
            correct += (predictions == labels).sum().item()
            total += labels.size(0)

    avg_loss = running_loss / len(loader.dataset)
    accuracy = correct / total if total else 0.0
    return avg_loss, accuracy


def main() -> None:
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    train_loader, val_loader, classes = get_dataloaders(
        data_dir=args.data_dir,
        batch_size=args.batch_size,
    )

    print("Loading FastViT-T12 model...")
    model = timm.create_model("fastvit_t12", pretrained=True, num_classes=len(classes))
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)

    best_val_acc = 0.0
    args.save_path.parent.mkdir(parents=True, exist_ok=True)

    for epoch in range(args.epochs):
        train_loss = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc = evaluate(model, val_loader, criterion, device)

        print(
            f"Epoch [{epoch + 1}/{args.epochs}] "
            f"Train Loss: {train_loss:.4f} | "
            f"Val Loss: {val_loss:.4f} | "
            f"Val Acc: {val_acc:.4f}"
        )

        if val_acc >= best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), args.save_path)
            print(f"Saved checkpoint to: {args.save_path}")

    print(f"Training complete. Best validation accuracy: {best_val_acc:.4f}")


if __name__ == "__main__":
    main()
