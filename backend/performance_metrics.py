import numpy as np
import torch


def get_eval_device(device: torch.device | str | None = None) -> torch.device:
    """Return CUDA device if available, otherwise CPU."""
    if device is not None:
        return torch.device(device)
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def compute_confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray, num_classes: int) -> np.ndarray:
    """Build confusion matrix where rows=true classes and cols=predicted classes."""
    cm = np.zeros((num_classes, num_classes), dtype=np.int64)
    for true_label, pred_label in zip(y_true, y_pred):
        cm[int(true_label), int(pred_label)] += 1
    return cm


def compute_metrics_from_confusion_matrix(cm: np.ndarray) -> dict:
    """
    Compute accuracy, macro precision, macro recall, and macro F1-score from confusion matrix.
    """
    true_positives = np.diag(cm).astype(np.float64)
    predicted_positives = cm.sum(axis=0).astype(np.float64)
    actual_positives = cm.sum(axis=1).astype(np.float64)

    precision_per_class = np.divide(
        true_positives,
        predicted_positives,
        out=np.zeros_like(true_positives),
        where=predicted_positives > 0,
    )
    recall_per_class = np.divide(
        true_positives,
        actual_positives,
        out=np.zeros_like(true_positives),
        where=actual_positives > 0,
    )
    f1_per_class = np.divide(
        2 * precision_per_class * recall_per_class,
        precision_per_class + recall_per_class,
        out=np.zeros_like(precision_per_class),
        where=(precision_per_class + recall_per_class) > 0,
    )

    accuracy = float(true_positives.sum() / max(cm.sum(), 1))
    precision_macro = float(np.mean(precision_per_class))
    recall_macro = float(np.mean(recall_per_class))
    f1_macro = float(np.mean(f1_per_class))

    return {
        "accuracy": accuracy,
        "precision": precision_macro,
        "recall": recall_macro,
        "f1_score": f1_macro,
        "precision_per_class": precision_per_class.tolist(),
        "recall_per_class": recall_per_class.tolist(),
        "f1_per_class": f1_per_class.tolist(),
    }


def evaluate_validation_loader(
    model: torch.nn.Module,
    val_loader,
    device: torch.device | str | None = None,
    class_names: list[str] | None = None,
) -> dict:
    """
    Evaluate model on validation DataLoader without gradient computation.

    Args:
        model: Trained model to evaluate.
        val_loader: Validation DataLoader (should be shuffled=False to avoid leakage/order drift).
        device: Optional evaluation device.
        class_names: Optional class names aligned with class indices.

    Returns:
        Dictionary with:
          - accuracy, precision, recall, f1_score
          - confusion_matrix
          - per-class precision/recall/f1
    """
    target_device = get_eval_device(device)
    model = model.to(target_device)
    model.eval()  # critical for leakage-safe validation (no training behavior)

    all_preds = []
    all_labels = []

    with torch.no_grad():  # no gradient computation during validation
        for images, labels in val_loader:
            images = images.to(target_device, non_blocking=True)
            labels = labels.to(target_device, non_blocking=True)

            outputs = model(images)
            preds = torch.argmax(outputs, dim=1)

            all_preds.append(preds.cpu())
            all_labels.append(labels.cpu())

    if not all_labels:
        raise ValueError("Validation DataLoader is empty")

    y_pred = torch.cat(all_preds).numpy()
    y_true = torch.cat(all_labels).numpy()

    if class_names is not None:
        num_classes = len(class_names)
    else:
        num_classes = int(max(np.max(y_true), np.max(y_pred)) + 1)
        class_names = [f"class_{i}" for i in range(num_classes)]

    cm = compute_confusion_matrix(y_true=y_true, y_pred=y_pred, num_classes=num_classes)
    metrics = compute_metrics_from_confusion_matrix(cm)

    result = {
        "accuracy": metrics["accuracy"],
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "f1_score": metrics["f1_score"],
        "confusion_matrix": cm.tolist(),
        "per_class": {
            class_name: {
                "precision": metrics["precision_per_class"][index],
                "recall": metrics["recall_per_class"][index],
                "f1_score": metrics["f1_per_class"][index],
            }
            for index, class_name in enumerate(class_names)
        },
    }

    return result
