from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns
import timm
import torch
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

from dataloader import get_dataloaders


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a trained FastViT model on validation data.")
    parser.add_argument("--data-dir", type=str, default="/content/Preprocess_data")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--model-name", type=str, default="fastvit_t12")
    parser.add_argument("--checkpoint", type=Path, default=Path("fastvit_t12_model.pth"))
    parser.add_argument("--cm-path", type=Path, default=Path("confusion_matrix.png"))
    parser.add_argument("--report-path", type=Path, default=Path("classification_report.json"))
    return parser.parse_args()


def evaluate_model(
    model: torch.nn.Module,
    loader: torch.utils.data.DataLoader,
    device: torch.device,
) -> tuple[list[int], list[int]]:
    model.eval()
    all_preds: list[int] = []
    all_labels: list[int] = []

    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)
            labels = labels.to(device)

            logits = model(images)
            preds = logits.argmax(dim=1)

            all_preds.extend(preds.cpu().tolist())
            all_labels.extend(labels.cpu().tolist())

    return all_preds, all_labels


def main() -> None:
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    _, val_loader, classes = get_dataloaders(data_dir=args.data_dir, batch_size=args.batch_size)

    if not args.checkpoint.exists():
        raise FileNotFoundError(f"Checkpoint not found: {args.checkpoint}")

    model = timm.create_model(args.model_name, pretrained=False, num_classes=len(classes))
    state_dict = torch.load(args.checkpoint, map_location=device)
    model.load_state_dict(state_dict)
    model = model.to(device)

    predictions, labels = evaluate_model(model, val_loader, device)

    accuracy = accuracy_score(labels, predictions)
    precision = precision_score(labels, predictions, average="weighted", zero_division=0)
    recall = recall_score(labels, predictions, average="weighted", zero_division=0)
    f1 = f1_score(labels, predictions, average="weighted", zero_division=0)

    print("\n===== PERFORMANCE METRICS =====")
    print(f"Accuracy  : {accuracy * 100:.2f}%")
    print(f"Precision : {precision:.4f}")
    print(f"Recall    : {recall:.4f}")
    print(f"F1 Score  : {f1:.4f}")

    report = classification_report(labels, predictions, target_names=classes, output_dict=True, zero_division=0)
    print("\n===== CLASSIFICATION REPORT =====")
    print(classification_report(labels, predictions, target_names=classes, zero_division=0))

    args.report_path.parent.mkdir(parents=True, exist_ok=True)
    with args.report_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)

    cm = confusion_matrix(labels, predictions)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=classes, yticklabels=classes)
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.title("Confusion Matrix")
    plt.tight_layout()

    args.cm_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(args.cm_path)

    print(f"\nConfusion matrix saved as: {args.cm_path}")
    print(f"Classification report saved as: {args.report_path}")


if __name__ == "__main__":
    main()
